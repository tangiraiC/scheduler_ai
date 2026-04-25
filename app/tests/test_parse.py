from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_parse_endpoint(monkeypatch) -> None:
    from app.api.v1.endpoints.parse import extraction_service

    async def fake_extract(raw_text: str):
        return {
            "success": True,
            "attempt": 1,
            "data": {
                "job_type": "workforce_schedule",
                "entities": {"employees": [], "shifts": []},
                "constraints": {"hard_constraints": [], "soft_constraints": []},
            },
        }

    monkeypatch.setattr(extraction_service, "extract", fake_extract)

    payload = {"raw_text": "Schedule a meeting for tomorrow."}
    response = client.post("/api/v1/parse", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert response.json()["extracted_data"]["job_type"] == "workforce_schedule"
