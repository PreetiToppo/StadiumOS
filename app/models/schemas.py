from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime

# --- Chat & Query schemas ---

class QueryRequest(BaseModel):
    query_text: str = Field(..., min_length=2, max_length=1000, description="The fan's query text or incident description.")
    user_id: str = Field(..., description="Unique identifier for the user.")
    session_id: Optional[str] = Field(None, description="Active session ID for tracking conversational state.")
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="Latitude location of the user inside the stadium.")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="Longitude location of the user inside the stadium.")

class QueryResponse(BaseModel):
    routed_to: str = Field(..., description="The service the query was routed to (e.g., 'RAG' or 'EMERGENCY').")
    response_text: str = Field(..., description="The computed response text or instant rescue guidelines.")
    confidence_score: float = Field(..., ge=0.0, le=1.0, description="The routing or matching confidence score.")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="The exact processing timestamp.")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional context or debugging parameters.")


# --- Emergency specific schemas ---

class EmergencyReport(BaseModel):
    incident_type: str = Field(..., description="Type of incident: e.g., Fire, Medical, Security, Crowd Control.")
    description: str = Field(..., min_length=5, description="Full description of the situation.")
    location: str = Field(..., description="Detailed location in the stadium (e.g., Gate 4, Section 102, Row M).")
    reported_by: str = Field(..., description="User ID or device ID of the reporter.")
    severity_override: Optional[str] = Field(None, description="Optional operator severity override (Low, Medium, High, Critical).")

class EmergencyResponse(BaseModel):
    incident_id: str = Field(..., description="Unique incident identifier.")
    escalated: bool = Field(True, description="Indicates if the emergency was escalated to the command center.")
    severity: str = Field(..., description="Assigned severity rating (Low, Medium, High, Critical).")
    dispatched_units: List[str] = Field(..., description="Units dispatched (e.g., Medical Team 2, Fire Marshall, Local Security).")
    safety_instructions: str = Field(..., description="Immediate instructions returned to the user for self-preservation.")
    estimated_response_time: str = Field(..., description="Estimated arrival time of security/medical staff (e.g., '2 minutes').")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# --- Venue RAG Document schemas ---

class VenueDocumentCreate(BaseModel):
    text: str = Field(..., min_length=5, description="The stadium text chunk containing operational details.")
    category: str = Field(..., description="Document classification (e.g., Restrooms, Food, Parking, Navigation).")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Metadata dictionary (e.g., gate_association, section).")

class VenueDocument(VenueDocumentCreate):
    id: str = Field(..., description="Unique document ID (e.g., UUID or hash).")
    created_at: datetime = Field(default_factory=datetime.utcnow)
