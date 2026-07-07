import pytest
from app.services.vector_store import InMemoryVectorStore
from app.models.schemas import VenueDocumentCreate

def test_vector_store_operations():
    """Tests basic addition, indexing, similarity search, and deletion in the vector store."""
    store = InMemoryVectorStore()
    
    # 1. Clear default pre-seeded documents to test cleanly
    with store.lock:
        store.documents.clear()
        store._rebuild_index()

    # 2. Add custom documents
    doc1 = store.add_document(VenueDocumentCreate(
        text="The pizza place serves cheese pizza and pepperoni pizza near Gate 5.",
        category="Food",
        metadata={"gate": 5}
    ))
    
    doc2 = store.add_document(VenueDocumentCreate(
        text="Find restrooms and baby changing tables at Section 109 corridor.",
        category="Facilities",
        metadata={"section": 109}
    ))

    # Assert documents are added
    assert len(store.documents) == 2
    assert doc1.id in store.documents
    assert doc2.id in store.documents

    # 3. Test similarity search (Exact terms match)
    results = store.search("Where is the pizza place?")
    assert len(results) > 0
    matched_doc, score = results[0]
    assert matched_doc.id == doc1.id
    assert score > 0.0

    # Test similarity search (Semantic/partial overlap)
    results_restroom = store.search("baby restrooms")
    assert len(results_restroom) > 0
    matched_doc_rr, score_rr = results_restroom[0]
    assert matched_doc_rr.id == doc2.id
    assert score_rr > 0.0

    # Test query with completely unrelated vocabulary
    results_unrelated = store.search("astronaut flying to mars")
    assert len(results_unrelated) == 0

    # 4. Test document deletion
    delete_success = store.delete_document(doc1.id)
    assert delete_success is True
    assert len(store.documents) == 1
    
    # After deletion, searching for pizza should yield no results
    results_after_delete = store.search("pizza")
    assert len(results_after_delete) == 0
