from fastapi import APIRouter, Request, HTTPException
from typing import List
from app.models.schemas import EmergencyReport, EmergencyResponse
from app.services.emergency import emergency_service
from app.rate_limiter import limiter

router = APIRouter(prefix="/api/v1/emergency", tags=["Emergency"])

@router.post("/report", response_model=EmergencyResponse, status_code=201)
@limiter.limit("30/minute")
async def report_emergency(request: Request, payload: EmergencyReport):
    """Allows fans or operators to submit emergency incidents directly, bypassing chat agents."""
    return emergency_service.process_report(payload)

@router.get("/incidents", response_model=List[EmergencyResponse])
async def get_all_active_incidents():
    """Lists all active logged emergency reports in the system. Typically restricted to admin dashboard console."""
    return emergency_service.get_all_incidents()

@router.get("/incidents/{incident_id}", response_model=EmergencyResponse)
async def get_incident_by_id(incident_id: str):
    """Retrieves current deployment details and instructions for a specific active emergency incident ID."""
    incident = emergency_service.get_incident(incident_id)
    if not incident:
        raise HTTPException(status_code=404, detail=f"Incident with ID {incident_id} not found.")
    return incident
