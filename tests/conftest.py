import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.vector_store import vector_store
from app.services.emergency import emergency_service

@pytest.fixture(autouse=True)
def reset_in_memory_stores():
    """Fixture that runs before every single test to reset RAG data and Emergency Incident Logs."""
    # Reset Vector Store
    with vector_store.lock:
        vector_store.documents.clear()
        vector_store._seed_default_data()
        
    # Reset Emergency Incidents registry
    with emergency_service._lock:
        emergency_service._incidents.clear()
    yield

@pytest.fixture
def client():
    """Provides a FastAPI test client instance."""
    with TestClient(app) as c:
        yield c
