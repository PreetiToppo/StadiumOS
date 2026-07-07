import uuid
import threading
from typing import Dict, List, Optional
from datetime import datetime
from app.models.schemas import EmergencyReport, EmergencyResponse

class EmergencyEscalationService:
    def __init__(self):
        self._incidents: Dict[str, EmergencyResponse] = {}
        self._lock = threading.Lock()

    def process_report(self, report: EmergencyReport) -> EmergencyResponse:
        """Processes an emergency report, classifies severity, dispatches units, and returns safety instructions."""
        incident_id = f"inc-{uuid.uuid4().hex[:8]}"
        desc_lower = report.description.lower()
        inc_type_lower = report.incident_type.lower()
        
        # 1. Determine severity
        severity = "Medium"
        if report.severity_override:
            severity = report.severity_override
        else:
            # Critical triggers
            if any(k in desc_lower or k in inc_type_lower for k in ["fire", "bomb", "explosion", "shooter", "shooting", "gun", "hostage", "terrorist"]):
                severity = "Critical"
            # High triggers
            elif any(k in desc_lower or k in inc_type_lower for k in ["heart attack", "unconscious", "collapse", "seizure", "bleeding", "choking", "stabbed", "knife"]):
                severity = "High"
            # Low triggers
            elif any(k in desc_lower or k in inc_type_lower for k in ["spill", "lost item", "wallet", "minor cut", "trash", "clean"]):
                severity = "Low"

        # 2. Dispatch Units & Instructions based on Severity & Type
        dispatched_units = []
        safety_instructions = "Please remain calm. Stadium crew has been alerted."
        estimated_response_time = "5 minutes"

        if severity == "Critical":
            estimated_response_time = "90 seconds"
            if "fire" in desc_lower or "fire" in inc_type_lower:
                dispatched_units = ["Fire Marshall Team Alpha", "First Aid Squad 1", "Stadium Police"]
                safety_instructions = "Evacuate the section immediately. Proceed to the nearest green-lit emergency exit (Gate A or B). Do not use lifts or elevators. Cover your nose with a damp cloth if smoke is present."
            elif any(k in desc_lower or k in inc_type_lower for k in ["shooter", "gun", "hostage", "shooting", "bomb", "terrorist", "explosion"]):
                dispatched_units = ["Tactical Response Unit", "Stadium Security Force", "Emergency Medical Response"]
                safety_instructions = "RUN: Evacuate the area if safe. HIDE: Silence your phone, lock doors, and seek immediate cover. FIGHT: Take action only as a last resort when in imminent danger."
            else:
                dispatched_units = ["Emergency Response Team", "Stadium Police Force"]
                safety_instructions = "Move away from the danger area. Follow instructions from stadium marshalls and public broadcasts."
                
        elif severity == "High":
            estimated_response_time = "3 minutes"
            dispatched_units = ["Medical Emergency Response Team (MERT)", "Section Security Officer"]
            if any(k in desc_lower or k in inc_type_lower for k in ["heart", "cardiac", "chest pain"]):
                safety_instructions = "Keep the patient calm and laying down. Medical team is en route. If trained, locate the nearest AED (available at Section 102 First Aid Desk)."
            elif "bleeding" in desc_lower:
                safety_instructions = "Apply firm, direct pressure to the wound using a clean cloth or bandage. Keep the injured limb elevated if possible."
            else:
                safety_instructions = "Do not move the patient unless they are in immediate danger. Clear the space around them to let them breathe. Help is on the way."

        elif severity == "Medium":
            estimated_response_time = "5 minutes"
            dispatched_units = ["Zone Security Guard", "Crowd Control Steward"]
            safety_instructions = "Security is on their way to inspect the section. Please stand clear and avoid escalating any active conflicts."

        else:  # Low
            estimated_response_time = "10 minutes"
            dispatched_units = ["Stadium Guest Services Officer", "Maintenance Team"]
            safety_instructions = "Thank you for reporting. Stadium management is tracking this issue. Safe enjoyment of the match is our priority."

        # 3. Store incident in-memory
        response = EmergencyResponse(
            incident_id=incident_id,
            escalated=True,
            severity=severity,
            dispatched_units=dispatched_units,
            safety_instructions=safety_instructions,
            estimated_response_time=estimated_response_time,
            timestamp=datetime.utcnow()
        )

        with self._lock:
            self._incidents[incident_id] = response

        return response

    def get_incident(self, incident_id: str) -> Optional[EmergencyResponse]:
        """Retrieves an active incident by its ID."""
        with self._lock:
            return self._incidents.get(incident_id)

    def get_all_incidents(self) -> List[EmergencyResponse]:
        """Retrieves all active incidents in the system."""
        with self._lock:
            return list(self._incidents.values())

# Global instance
emergency_service = EmergencyEscalationService()
