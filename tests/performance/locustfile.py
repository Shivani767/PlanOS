"""Locust load test for PlanOS (Phase 25).

Run against a running API (default http://localhost:8000):

    locust -f tests/performance/locustfile.py --headless -u 100 -r 10 -t 60s

Measures plan/scenario list throughput and p50/p95/p99 latency. Results are
written to docs/PERFORMANCE.md after each real run (never invented numbers).
"""

from __future__ import annotations

import uuid

from locust import HttpUser, between, task


class PlanOSUser(HttpUser):
    """Simulates an authenticated planner exercising read-heavy endpoints."""

    wait_time = between(0.1, 0.5)

    email: str
    # Throwaway load-test credential only; real secrets never live in code.
    password: str = "password123"  # noqa: S105
    token: str | None = None

    def on_start(self) -> None:
        suffix = uuid.uuid4().hex[:10]
        self.email = f"load-{suffix}@example.com"
        resp = self.client.post(
            "/api/v1/auth/register",
            json={
                "email": self.email,
                "password": self.password,
                "full_name": "Load User",
                "organization_slug": f"load-{suffix}",
            },
        )
        if resp.status_code not in (201, 422):
            return
        login = self.client.post(
            "/api/v1/auth/login",
            json={"email": self.email, "password": self.password},
        )
        if login.status_code == 200:
            self.token = login.json().get("access_token")

    def _headers(self) -> dict[str, str]:
        return (
            {"Authorization": f"Bearer {self.token}"}
            if self.token
            else {"Authorization": "Bearer anonymous"}
        )

    @task(5)
    def list_plans(self) -> None:
        self.client.get("/api/v1/plans", headers=self._headers())

    @task(5)
    def list_scenarios(self) -> None:
        self.client.get("/api/v1/scenarios", headers=self._headers())

    @task(2)
    def get_metrics(self) -> None:
        self.client.get("/api/v1/metrics/summary")

    @task(1)
    def get_health(self) -> None:
        self.client.get("/health")

    @task(1)
    def get_knowledge_search(self) -> None:
        self.client.get(
            "/api/v1/knowledge/search",
            params={"q": "planning", "top_k": 3},
            headers=self._headers(),
        )
