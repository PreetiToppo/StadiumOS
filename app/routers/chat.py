from fastapi import APIRouter, Request
from app.models.schemas import QueryRequest, QueryResponse
from app.services.agent_router import agent_router
from app.rate_limiter import limiter
from app.config import settings

router = APIRouter(prefix="/api/v1/chat", tags=["Chat"])

@router.post("/query", response_model=QueryResponse)
@limiter.limit(settings.DEFAULT_RATE_LIMIT)
async def route_user_query(request: Request, payload: QueryRequest):
    """Processes incoming queries. Routes them dynamically to standard RAG or Emergency services."""
    return agent_router.route_query(payload)
