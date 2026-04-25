from app.services.schedule_service import ScheduleService


def test_schedule_service_full_pipeline(monkeypatch) -> None:
    service = ScheduleService()

    async def fake_extract(_raw_text: str) -> dict:
        return {
            "success": True,
            "attempt": 1,
            "data": {
                "job_type": "workforce_schedule",
                "entities": {
                    "employees": [
                        {
                            "name": "Alice",
                            "skills": ["front_desk"],
                            "availability": ["monday"],
                        },
                        {
                            "name": "Bob",
                            "skills": ["front_desk"],
                            "availability": ["monday"],
                        },
                    ],
                    "shifts": [
                        {
                            "id": "shift_1",
                            "day": "monday",
                            "start_time": "09:00",
                            "end_time": "13:00",
                            "location": "apt_a",
                            "required_skills": ["front_desk"],
                            "min_staff": 1,
                            "max_staff": 1,
                        },
                        {
                            "id": "shift_2",
                            "day": "monday",
                            "start_time": "13:00",
                            "end_time": "17:00",
                            "location": "apt_b",
                            "required_skills": ["front_desk"],
                            "min_staff": 1,
                            "max_staff": 1,
                        },
                    ],
                },
                "constraints": {
                    "hard_constraints": ["max_40_hours_per_7_days"],
                    "soft_constraints": [],
                },
            },
        }

    monkeypatch.setattr(service.extraction_service, "extract", fake_extract)

    import asyncio

    result = asyncio.run(
        service.run(
            raw_text="Create a Monday front desk schedule.",
            strategy="largest_first",
        )
    )

    assert result["status"] == "success"
    assert "final_schedule" in result
    assert "validation" in result
    assert "is_valid" in result
    assert result["stage_trace"][-1]["stage"] == "validation"
