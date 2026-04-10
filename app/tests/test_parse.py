from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_parse_endpoint(monkeypatch) -> None:
    async def fake_extract(self, raw_text: str):
        return {
            "success": True,
            "attempt": 1,
            "data": {
                "job_type": "workforce_schedule",
                "entities": {"employees": [], "shifts": []},
                "constraints": {"hard_constraints": [], "soft_constraints": []},
            },
        }

    monkeypatch.setattr("app.api.v1.endpoints.parse.ExtractionService.extract", fake_extract)

    payload = {"raw_text": "Schedule a meeting for tomorrow."}
    response = client.post("/api/v1/parse", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "parsed"
    assert response.json()["extracted_constraints"]["job_type"] == "workforce_schedule"
