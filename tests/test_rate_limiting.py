from fastapi.testclient import TestClient

def test_rate_limiting_chat_query(client: TestClient):
    """Verify that rapid concurrent requests eventually trigger an HTTP 429 Rate Limit response."""
    payload = {
        "query_text": "Is there a souvenir shop nearby?",
        "user_id": "fan-limit-test"
    }
    
    triggered_429 = False
    rate_limit_details = None

    # Default rate limit is 60/minute.
    # Send 70 requests rapidly to exceed the limit.
    for i in range(75):
        response = client.post("/api/v1/chat/query", json=payload)
        if response.status_code == 429:
            triggered_429 = True
            rate_limit_details = response.json()
            break
            
    assert triggered_429 is True, "Rate limiter did not trigger after 75 rapid requests."
    assert rate_limit_details["error"] == "Too Many Requests"
    assert "Global rate limit exceeded" in rate_limit_details["message"]
    assert "limit" in rate_limit_details
