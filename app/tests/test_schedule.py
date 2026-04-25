from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_schedule_endpoint(monkeypatch) -> None:
    from app.api.v1.endpoints.schedule import job_service

    monkeypatch.setattr(job_service, "create_job", lambda _payload: "job_test")

    payload = {
        "constraints": {
            "job_type": "workforce_schedule",
            "entities": {
                "employees": [
                    {
                        "name": "alice",
                        "skills": ["front_desk"],
                        "availability": ["monday_morning"],
                        "max_shifts_per_week": 5,
                        "cannot_work_with": [],
                    }
                ],
                "shifts": [
                    {
                        "id": "shift_1",
                        "day": "monday",
                        "time": "morning",
                        "location": "clinic_a",
                        "required_skills": ["front_desk"],
                        "min_staff": 1,
                        "max_staff": 1,
                    }
                ],
            },
            "constraints": {
                "hard_constraints": ["respect availability"],
                "soft_constraints": ["balance workload"],
            },
        }
    }
    response = client.post("/api/v1/schedule", json=payload)
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["is_valid"] is True
    assert "nodes" in body["schedule_result"]
    assert "job_id" in body
