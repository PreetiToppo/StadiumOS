import re
import uuid
import numpy as np
import threading
from typing import List, Tuple, Dict, Any, Optional
from datetime import datetime
from app.models.schemas import VenueDocument, VenueDocumentCreate

# Simple English stop words to filter out noise
STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", "aren't",
    "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", "but", "by", "can't",
    "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", "doing", "don't", "down", "during",
    "each", "few", "for", "from", "further", "had", "hadn't", "has", "hasn't", "have", "haven't", "having",
    "he", "he'd", "he'll", "he's", "her", "here", "here's", "hers", "herself", "him", "himself", "his", "how",
    "how's", "i", "i'd", "i'll", "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself",
    "let's", "me", "more", "most", "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on", "once",
    "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", "same", "shan't", "she",
    "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", "such", "than", "that", "that's", "the",
    "their", "theirs", "them", "themselves", "then", "there", "there's", "these", "they", "they'd", "they'll",
    "they're", "they've", "this", "those", "through", "to", "too", "under", "until", "up", "very", "was",
    "wasn't", "we", "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's", "when", "when's",
    "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with", "won't", "would",
    "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", "yours", "yourself", "yourselves"
}

class InMemoryVectorStore:
    def __init__(self):
        self.documents: Dict[str, VenueDocument] = {}
        self.vocab: Dict[str, int] = {}
        self.idf: np.ndarray = np.array([])
        self.doc_vectors: np.ndarray = np.empty((0, 0))  # Shape: (Num_Docs, Vocab_Size)
        self.lock = threading.Lock()
        self._seed_default_data()

    def _tokenize(self, text: str) -> List[str]:
        """Cleans, lowercases, tokenizes, and filters stop words."""
        clean_text = re.sub(r'[^\w\s]', '', text.lower())
        tokens = clean_text.split()
        return [t for t in tokens if t not in STOP_WORDS and len(t) > 1]

    def _rebuild_index(self):
        """Rebuilds the vocabulary, IDF, and TF-IDF document vectors from scratch.
        Must be called inside the lock.
        """
        doc_list = list(self.documents.values())
        if not doc_list:
            self.vocab = {}
            self.idf = np.array([])
            self.doc_vectors = np.empty((0, 0))
            return

        # 1. Build vocabulary
        vocab = {}
        doc_tokens = []
        for doc in doc_list:
            tokens = self._tokenize(doc.text)
            doc_tokens.append(tokens)
            for token in tokens:
                if token not in vocab:
                    vocab[token] = len(vocab)
        
        self.vocab = vocab
        vocab_size = len(vocab)
        num_docs = len(doc_list)

        if vocab_size == 0:
            self.idf = np.array([])
            self.doc_vectors = np.zeros((num_docs, 0))
            return

        # 2. Compute Document Frequency (DF) for each term
        df = np.zeros(vocab_size)
        for tokens in doc_tokens:
            unique_tokens = set(tokens)
            for t in unique_tokens:
                if t in vocab:
                    df[vocab[t]] += 1

        # 3. Compute Inverse Document Frequency (IDF) using scikit-learn style smoothing
        self.idf = np.log((1 + num_docs) / (1 + df)) + 1.0

        # 4. Compute TF-IDF matrix (Normalized)
        tf_idf_matrix = np.zeros((num_docs, vocab_size))
        for doc_idx, tokens in enumerate(doc_tokens):
            if not tokens:
                continue
            # Term counts in this document
            counts = {}
            for t in tokens:
                counts[t] = counts.get(t, 0) + 1
            
            # Populate TF-IDF values
            for term, count in counts.items():
                term_idx = vocab[term]
                tf = count  # Raw term frequency
                tf_idf_matrix[doc_idx, term_idx] = tf * self.idf[term_idx]

            # Normalize document vector to L2 unit length
            norm = np.linalg.norm(tf_idf_matrix[doc_idx])
            if norm > 0:
                tf_idf_matrix[doc_idx] /= norm

        self.doc_vectors = tf_idf_matrix

    def add_document(self, doc_in: VenueDocumentCreate) -> VenueDocument:
        """Adds a document to the index and rebuilds the representations."""
        with self.lock:
            doc_id = str(uuid.uuid4())
            doc = VenueDocument(
                id=doc_id,
                text=doc_in.text,
                category=doc_in.category,
                metadata=doc_in.metadata,
                created_at=datetime.utcnow()
            )
            self.documents[doc_id] = doc
            self._rebuild_index()
            return doc

    def delete_document(self, doc_id: str) -> bool:
        """Deletes a document from the index by ID."""
        with self.lock:
            if doc_id in self.documents:
                del self.documents[doc_id]
                self._rebuild_index()
                return True
            return False

    def search(self, query: str, top_k: int = 3) -> List[Tuple[VenueDocument, float]]:
        """Searches for top-K matching documents using cosine similarity on TF-IDF vectors."""
        with self.lock:
            if not self.documents or not self.vocab:
                return []

            # 1. Tokenize query
            tokens = self._tokenize(query)
            if not tokens:
                return []

            # 2. Build query vector
            query_vector = np.zeros(len(self.vocab))
            counts = {}
            for t in tokens:
                if t in self.vocab:
                    counts[t] = counts.get(t, 0) + 1

            for term, count in counts.items():
                term_idx = self.vocab[term]
                query_vector[term_idx] = count * self.idf[term_idx]

            # 3. L2 Normalize query vector
            q_norm = np.linalg.norm(query_vector)
            if q_norm == 0:
                return []
            query_vector /= q_norm

            # 4. Calculate Cosine Similarity (dot product since vectors are normalized)
            similarities = self.doc_vectors.dot(query_vector)

            # 5. Sort matches
            top_indices = np.argsort(similarities)[::-1][:top_k]
            
            results = []
            doc_list = list(self.documents.values())
            for idx in top_indices:
                score = float(similarities[idx])
                if score > 0.0:  # Only return documents with some semantic match
                    results.append((doc_list[idx], score))
            
            return results

    def _seed_default_data(self):
        """Pre-seeds the vector store with standard smart stadium venue data."""
        seeds = [
            VenueDocumentCreate(
                text="Taco Stand 'Azteca' is located at Gate 3. Serving authentic Mexican tacos, burritos, and cold soft drinks. Quick checkout with smart mobile pay.",
                category="Food & Beverage",
                metadata={"location": "Gate 3", "vendor": "Azteca"}
            ),
            VenueDocumentCreate(
                text="The Official FIFA World Cup 2026 Merchandise Store is located at Section 105 near the main concourse. It sells official jerseys, balls, caps, and souvenirs.",
                category="Retail",
                metadata={"location": "Section 105", "vendor": "FIFA Store"}
            ),
            VenueDocumentCreate(
                text="Medical Room and First Aid Clinic is situated at Section 102 near Gate B. Equipped with emergency equipment, AEDs, and certified first responders.",
                category="Safety & Health",
                metadata={"location": "Section 102", "room": "First Aid Clinic"}
            ),
            VenueDocumentCreate(
                text="All-gender restrooms and accessible toilet facilities are located at Section 104 (lower level) and Section 208 (upper balcony level). All have baby changing rooms.",
                category="Facilities",
                metadata={"location": "Section 104 & 208", "type": "Restrooms"}
            ),
            VenueDocumentCreate(
                text="Gate A (North Gate) leads directly to the Light Rail Transit station and ride-sharing pickup zone. Best exit for public transport riders.",
                category="Navigation",
                metadata={"location": "Gate A", "exit_to": "Light Rail"}
            ),
            VenueDocumentCreate(
                text="Lost and Found Center is located at the Guest Services desk near Section 112. Report lost items or children to officers here.",
                category="Facilities",
                metadata={"location": "Section 112", "desk": "Guest Services"}
            )
        ]
        # Avoid calling rebuild_index on every document inside init
        for i, seed in enumerate(seeds):
            doc_id = f"seed-doc-{i}"
            doc = VenueDocument(
                id=doc_id,
                text=seed.text,
                category=seed.category,
                metadata=seed.metadata,
                created_at=datetime.utcnow()
            )
            self.documents[doc_id] = doc
        
        self._rebuild_index()

# Global thread-safe instance
vector_store = InMemoryVectorStore()
