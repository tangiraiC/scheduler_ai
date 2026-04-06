from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_parse_endpoint() -> None:
    payload = {"text": "Schedule a meeting for tomorrow."}
    response = client.post("/api/v1/parse", json=payload)
    assert response.status_code == 200
    assert response.json()["input_text"] == payload["text"]

