from fastapi import APIRouter, HTTPException, Request
from typing import List
from app.models.schemas import VenueDocument, VenueDocumentCreate
from app.services.vector_store import vector_store
from app.rate_limiter import limiter

router = APIRouter(prefix="/api/v1/venue", tags=["Venue Data"])

@router.post("/documents", response_model=VenueDocument, status_code=201)
async def create_venue_document(payload: VenueDocumentCreate):
    """Ingests a new venue text chunk, computes TF-IDF weights, and updates the RAG store."""
    return vector_store.add_document(payload)

@router.delete("/documents/{doc_id}", status_code=200)
async def delete_venue_document(doc_id: str):
    """Removes a document from the RAG store by ID and updates vocabulary weights."""
    success = vector_store.delete_document(doc_id)
    if not success:
        raise HTTPException(status_code=404, detail=f"Document with ID {doc_id} not found.")
    return {"status": "success", "message": f"Document {doc_id} deleted successfully."}

@router.get("/documents", response_model=List[VenueDocument])
async def list_venue_documents():
    """Lists all raw venue documents stored in the system."""
    return list(vector_store.documents.values())

@router.get("/search")
@limiter.limit("100/minute")
async def search_venue(request: Request, q: str, limit: int = 3):
    """Searches the vector store directly, returning document details and semantic matching similarity scores."""
    if not q:
        raise HTTPException(status_code=400, detail="Query parameter 'q' is required.")
    
    results = vector_store.search(q, top_k=limit)
    return [
        {
            "document": doc,
            "similarity_score": round(score, 4)
        }
        for doc, score in results
    ]
