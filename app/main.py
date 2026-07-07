from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.rate_limiter import limiter
from app.routers import chat, emergency, venue

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="FastAPI Backend for FIFA World Cup 2026 Smart Stadiums Operations and Routing Platform."
)

# Set up SlowAPI state and exception handler
app.state.limiter = limiter
@app.exception_handler(RateLimitExceeded)
def custom_rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom response structure when a client hits the rate limit."""
    return JSONResponse(
        status_code=429,
        content={
            "error": "Too Many Requests",
            "message": "Global rate limit exceeded. Please back off and retry later.",
            "limit": exc.detail
        }
    )

# Register routes
app.include_router(chat.router)
app.include_router(emergency.router)
app.include_router(venue.router)

@app.get("/", tags=["General"])
async def root():
    """Service status and meta information."""
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "environment": settings.ENVIRONMENT,
        "supported_features": [
            "Agentic Query Routing",
            "Local In-Memory RAG Vector Store",
            "Global Rate Limiting",
            "Pydantic V2 Input Validation",
            "Emergency Escalation Workflow"
        ]
    }
