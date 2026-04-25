from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health() -> None:
    response = client.get("/api/v1/health")

    assert response.status_code == 200
    assert "status" in response.json()
    assert "services" in response.json()


def test_parse(monkeypatch) -> None:
    from app.api.v1.endpoints.parse import extraction_service

    def fake_extract(raw_text: str) -> dict:
        return {
            "job_type": "workforce_schedule",
            "entities": {"employees": [], "shifts": []},
            "constraints": {"hard_constraints": [], "soft_constraints": []},
        }

    monkeypatch.setattr(extraction_service, "extract", fake_extract)

    response = client.post(
        "/api/v1/parse",
        json={
            "raw_text": "Create a schedule.",
            "domain": "workforce_schedule",
            "metadata": {},
        },
    )

    assert response.status_code == 200
    assert response.json()["status"] == "success"


def test_schedule_and_job_lookup(monkeypatch) -> None:
    from app.api.v1.endpoints.schedule import schedule_service
    from app.api.v1.endpoints.schedule import job_service as schedule_job_service
    from app.api.v1.endpoints.jobs import job_service as lookup_job_service

    saved_jobs = {}

    async def fake_run(raw_text: str, strategy: str, metadata: dict) -> dict:
        return {
            "status": "success",
            "input": {
                "raw_text": raw_text,
                "strategy": strategy,
                "metadata": metadata,
            },
            "extracted_data": {},
            "normalized_data": {},
            "graph_summary": {"node_count": 1, "edge_count": 0, "color_count": 1},
            "schedule_result": {},
            "validation": {
                "is_valid": True,
                "error_count": 0,
                "warning_count": 0,
                "errors": [],
                "warnings": [],
            },
            "final_schedule": {"days": {}, "total_assignments": 0},
            "is_valid": True,
        }

    def fake_create_job(payload: dict) -> str:
        saved_jobs["job_test"] = payload
        return "job_test"

    def fake_get_job(job_id: str) -> dict:
        return saved_jobs[job_id]

    monkeypatch.setattr(schedule_service, "run", fake_run)
    monkeypatch.setattr(schedule_job_service, "create_job", fake_create_job)
    monkeypatch.setattr(lookup_job_service, "get_job", fake_get_job)

    response = client.post(
        "/api/v1/schedule",
        json={
            "raw_text": "Create a schedule.",
            "strategy": "largest_first",
            "metadata": {},
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert "job_id" in body

    lookup = client.get(f"/api/v1/jobs/{body['job_id']}")
    assert lookup.status_code == 200
    assert lookup.json()["status"] == "success"
