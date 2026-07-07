import re
from datetime import datetime
from typing import Dict, Any
from app.config import settings
from app.models.schemas import QueryRequest, QueryResponse, EmergencyReport
from app.services.vector_store import vector_store
from app.services.emergency import emergency_service

class AgenticRouterService:
    def _is_emergency_query(self, query_text: str) -> bool:
        """Determines if a query is a critical emergency using optimized keyword heuristics."""
        cleaned = re.sub(r'[^\w\s]', ' ', query_text.lower())
        words = set(cleaned.split())
        
        for kw in settings.EMERGENCY_KEYWORDS:
            kw_clean = kw.lower()
            # If the keyword is a phrase (e.g., "heart attack"), check substring containment
            if " " in kw_clean:
                if kw_clean in cleaned:
                    return True
            else:
                # Direct word-level match to prevent false positives (e.g., "firewall" containing "fire")
                if kw_clean in words:
                    return True
        return False

    def route_query(self, request: QueryRequest) -> QueryResponse:
        """Core routing engine that directs the query to either the RAG or Emergency services."""
        query = request.query_text
        
        # 1. Check for Emergency Route
        if self._is_emergency_query(query):
            # Parse emergency details from request
            emergency_report = EmergencyReport(
                incident_type="Automatic Agent Router Escalation",
                description=query,
                location=f"Coordinates: Lat {request.latitude or 'Unknown'}, Lon {request.longitude or 'Unknown'}",
                reported_by=request.user_id
            )
            
            # Fire the emergency workflow
            esc_response = emergency_service.process_report(emergency_report)
            
            # Return immediate response with emergency details mapped in metadata
            return QueryResponse(
                routed_to="EMERGENCY",
                response_text=(
                    f"⚠️ CRITICAL ALERT REDIRECTED TO STADIUM DISPATCH: {esc_response.safety_instructions} "
                    f"Our Emergency Response Team ({', '.join(esc_response.dispatched_units)}) is en route. "
                    f"Estimated arrival: {esc_response.estimated_response_time}."
                ),
                confidence_score=1.0,
                timestamp=datetime.utcnow(),
                metadata={
                    "incident_id": esc_response.incident_id,
                    "severity": esc_response.severity,
                    "dispatched_units": esc_response.dispatched_units,
                    "estimated_arrival": esc_response.estimated_response_time
                }
            )

        # 2. RAG Route (Search local vector store)
        matches = vector_store.search(query, top_k=2)
        if matches:
            top_doc, score = matches[0]
            
            # Simple synthesis step mimicking an LLM answer generation using the doc context
            response_text = f"Based on stadium maps and venue data: {top_doc.text}"
            
            # If there's a secondary match with decent similarity, we add it as context
            additional_context = []
            if len(matches) > 1 and matches[1][1] > 0.3:
                additional_context.append(matches[1][0].text)

            return QueryResponse(
                routed_to="RAG",
                response_text=response_text,
                confidence_score=round(score, 4),
                timestamp=datetime.utcnow(),
                metadata={
                    "matched_document_ids": [doc.id for doc, _ in matches],
                    "all_scores": [round(s, 4) for _, s in matches],
                    "additional_context": additional_context
                }
            )

        # 3. Fallback Route (General assistant)
        return QueryResponse(
            routed_to="GENERAL_ASSISTANT",
            response_text="I couldn't locate specific information about that query. Please visit the Guest Services Desk at Section 112 or consult a nearby stadium marshal.",
            confidence_score=0.0,
            timestamp=datetime.utcnow(),
            metadata={"status": "no_match_found"}
        )

# Global instance
agent_router = AgenticRouterService()
