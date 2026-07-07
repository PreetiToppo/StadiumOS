from locust import HttpUser, task, between, tag
import random

class StadiumOSLoadTester(HttpUser):
    # Simulates realistic fan behavior: waiting 0.5 to 2 seconds between actions
    wait_time = between(0.5, 2.0)

    @tag('chat')
    @task(7)  # 70% of total concurrent traffic
    def simulate_fan_queries(self):
        queries = [
            "Where is the nearest wheelchair accessible entry gate?",
            "How frequently do the rapid transit shuttles run from Gate B?",
            "Where can I find a restroom near section 105?",
            "What concessions are active near Gate A?"
        ]
        self.client.post("/api/v1/chat/query", json={
            "query": random.choice(queries),
            "user_role": "fan"
        })

    @tag('emergency')
    @task(1)  # 10% of traffic - testing high priority short-circuit performance
    def simulate_critical_incidents(self):
        emergencies = [
            {"query": "🚨 MEDICAL EMERGENCY: Heart attack near section 112!", "user_role": "staff"},
            {"query": "Fire risk and smoke detected in the northern plaza egress area", "user_role": "volunteer"}
        ]
        chosen = random.choice(emergencies)
        self.client.post("/api/v1/emergency/report", json=chosen)

    @tag('abuse')
    @task(2)  # 20% of traffic - forces endpoints to hit slowapi rate-limits (HTTP 429)
    def simulate_api_flooding(self):
        # Rapid, back-to-back spamming to validate rate-limiter efficiency under load
        for _ in range(5):
            self.client.post("/api/v1/chat/query", json={
                "query": "spam_request_attack_payload",
                "user_role": "anonymous_bot"
            })