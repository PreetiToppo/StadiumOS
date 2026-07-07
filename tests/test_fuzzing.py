import pytest
from hypothesis import given, strategies as st
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

@given(
    malicious_text=st.text(min_size=0, max_size=1000),
    random_role=st.text(min_size=1, max_size=50)
)
def test_pydantic_boundary_fuzzing(malicious_text, random_role):
    """
    Throws infinite variations of random/malicious Unicode, emoji strings, 
    and null bytes to verify the API safely handles bad data without unhandled crashes.
    """
    payload = {
        "query": malicious_text,
        "user_role": random_role
    }
    response = client.post("/api/v1/chat/query", json=payload)
    
    # Assertions: Enterprise software must return structured error validation (4xx) 
    # or process successfully (200). It must NEVER crash with a raw Unhandled 500 Server Error.
    assert response.status_code in [200, 400, 422, 429]