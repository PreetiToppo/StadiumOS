from fastapi.testclient import TestClient

def test_route_rag_concession(client: TestClient):
    """Verify that queries about concessions are routed to the RAG vector store."""
    payload = {
        "query_text": "Where is the taco stand and what do they serve?",
        "user_id": "fan-123",
        "latitude": 34.0522,
        "longitude": -118.2437
    }
    response = client.post("/api/v1/chat/query", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["routed_to"] == "RAG"
    assert "taco" in data["response_text"].lower()
    assert data["confidence_score"] > 0.0
    assert len(data["metadata"]["matched_document_ids"]) > 0

def test_route_emergency_fire(client: TestClient):
    """Verify that active fire incidents are immediately escalated to the emergency dispatch."""
    payload = {
        "query_text": "There is a fire starting near gate 3! Send help!",
        "user_id": "fan-999",
        "latitude": 34.0528,
        "longitude": -118.2445
    }
    response = client.post("/api/v1/chat/query", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["routed_to"] == "EMERGENCY"
    assert "critical alert" in data["response_text"].lower()
    assert "evacuate" in data["response_text"].lower()
    assert data["confidence_score"] == 1.0
    assert data["metadata"]["severity"] == "Critical"
    assert "incident_id" in data["metadata"]

def test_route_emergency_medical(client: TestClient):
    """Verify that chest pain / heart attack symptoms trigger medical team dispatch."""
    payload = {
        "query_text": "I think someone is having a heart attack at Section 102!",
        "user_id": "fan-888"
    }
    response = client.post("/api/v1/chat/query", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["routed_to"] == "EMERGENCY"
    assert data["metadata"]["severity"] == "High"
    assert "MERT" in data["response_text"]
    assert "AED" in data["response_text"]

def test_route_general_fallback(client: TestClient):
    """Verify that general out-of-scope questions go to the fallback general assistant."""
    payload = {
        "query_text": "Can you explain the offside rule in soccer?",
        "user_id": "fan-555"
    }
    response = client.post("/api/v1/chat/query", json=payload)
    assert response.status_code == 200
    
    data = response.json()
    assert data["routed_to"] == "GENERAL_ASSISTANT"
    assert data["confidence_score"] == 0.0
    assert "guest services" in data["response_text"].lower()
