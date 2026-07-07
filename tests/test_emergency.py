from fastapi.testclient import TestClient

def test_direct_emergency_report_critical(client: TestClient):
    """Verify that a direct report of a bomb threat is classified as Critical with correct response schema."""
    payload = {
        "incident_type": "Security Threat",
        "description": "Suspicious package resembling a bomb found under seat 12.",
        "location": "Section 114, Row F",
        "reported_by": "guard-02"
    }
    response = client.post("/api/v1/emergency/report", json=payload)
    assert response.status_code == 201
    
    data = response.json()
    assert data["incident_id"].startswith("inc-")
    assert data["escalated"] is True
    assert data["severity"] == "Critical"
    assert "Tactical Response Unit" in data["dispatched_units"]
    assert "estimated_response_time" in data
    assert "RUN: Evacuate" in data["safety_instructions"]

def test_direct_emergency_report_low(client: TestClient):
    """Verify that reporting a water spill assigns a Low severity and dispatches maintenance."""
    payload = {
        "incident_type": "Maintenance",
        "description": "Large water spill causing slipping hazard near entrance.",
        "location": "Gate A concession area",
        "reported_by": "cleaner-12"
    }
    response = client.post("/api/v1/emergency/report", json=payload)
    assert response.status_code == 201
    
    data = response.json()
    assert data["severity"] == "Low"
    assert "Maintenance Team" in data["dispatched_units"]
    assert "stadium management is tracking" in data["safety_instructions"].lower()

def test_list_and_retrieve_incidents(client: TestClient):
    """Verify that all logged emergency incidents can be listed and retrieved individually."""
    # 1. Post two incidents
    incident_1 = {
        "incident_type": "Medical",
        "description": "Someone passed out and is unconscious at section 104.",
        "location": "Section 104",
        "reported_by": "fan-11"
    }
    incident_2 = {
        "incident_type": "Fire",
        "description": "Small trash can fire near Gate B.",
        "location": "Gate B",
        "reported_by": "steward-05"
    }
    res1 = client.post("/api/v1/emergency/report", json=incident_1)
    res2 = client.post("/api/v1/emergency/report", json=incident_2)
    
    id1 = res1.json()["incident_id"]
    id2 = res2.json()["incident_id"]

    # 2. List all incidents
    list_res = client.get("/api/v1/emergency/incidents")
    assert list_res.status_code == 200
    all_incidents = list_res.json()
    assert len(all_incidents) == 2
    
    incident_ids = [inc["incident_id"] for inc in all_incidents]
    assert id1 in incident_ids
    assert id2 in incident_ids

    # 3. Retrieve specific incident
    get_res = client.get(f"/api/v1/emergency/incidents/{id1}")
    assert get_res.status_code == 200
    assert get_res.json()["severity"] == "High"  # "unconscious" triggers High severity

    # 4. Retrieve invalid incident
    get_invalid = client.get("/api/v1/emergency/incidents/inc-nonexistent")
    assert get_invalid.status_code == 404
    assert "not found" in get_invalid.json()["detail"].lower()
