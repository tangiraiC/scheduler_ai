from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_schedule_endpoint() -> None:
    payload = {"constraints": ["morning", "team available"]}
    response = client.post("/api/v1/schedule", json=payload)
    assert response.status_code == 200
    assert "nodes" in response.json()["schedule"]
