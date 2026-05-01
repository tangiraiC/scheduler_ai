import asyncio

from app.services.extraction_service import ExtractionService


def test_extraction(monkeypatch):
    def fake_generate(self, system_prompt: str, user_prompt: str):
        return """
        {
          "job_type": "workforce_schedule",
          "entities": {
            "employees": [],
            "shifts": []
          },
          "constraints": {
            "hard_constraints": ["max_40_hours_per_7_days"],
            "soft_constraints": []
          }
        }
        """

    monkeypatch.setattr("app.services.lmstudio_client.LMStudioClient.generate", fake_generate)

    text = """
    There are front desk attendants. Some require certification.
    Some cannot work weekends. Max 40 hours per week.
    Shifts are 8 hours.
    """

    result = asyncio.run(ExtractionService().extract(text))

    assert result["success"] is True
    assert result["data"]["job_type"] == "workforce_schedule"
    assert "max_40_hours_per_7_days" in result["data"]["constraints"]["hard_constraints"]


def test_extraction_accepts_json_with_trailing_text(monkeypatch):
    def fake_generate(self, system_prompt: str, user_prompt: str):
        return """
        {
          "job_type": "workforce_schedule",
          "entities": {
            "employees": [],
            "shifts": []
          },
          "constraints": {
            "hard_constraints": [],
            "soft_constraints": [],
            "cannot_work_with_pairs": []
          },
          "edges": []
        }
        Extra response text that should be ignored.
        """

    monkeypatch.setattr("app.services.lmstudio_client.LMStudioClient.generate", fake_generate)

    result = asyncio.run(ExtractionService().extract("No scheduling information."))

    assert result["success"] is True
    assert result["data"]["edges"] == []


def test_extraction_coerces_scalar_list_fields(monkeypatch):
    def fake_generate(self, system_prompt: str, user_prompt: str):
        return """
        {
          "job_type": "workforce_schedule",
          "entities": {
            "employees": [
              {
                "name": "Alice",
                "skills": "front_desk",
                "availability": "Monday morning",
                "cannot_work_with": "Bob"
              }
            ],
            "shifts": [
              {
                "id": "shift_1",
                "day": "Monday",
                "time": "morning",
                "required_skills": "front_desk"
              }
            ]
          },
          "constraints": {
            "hard_constraints": "respect availability",
            "soft_constraints": []
          },
          "edges": []
        }
        """

    monkeypatch.setattr("app.services.lmstudio_client.LMStudioClient.generate", fake_generate)

    result = asyncio.run(ExtractionService().extract("Schedule Alice Monday morning."))

    employee = result["data"]["entities"]["employees"][0]
    shift = result["data"]["entities"]["shifts"][0]
    assert employee["skills"] == ["front_desk"]
    assert employee["availability"] == ["Monday morning"]
    assert employee["cannot_work_with"] == ["Bob"]
    assert shift["required_skills"] == ["front_desk"]
    assert result["data"]["constraints"]["hard_constraints"] == ["respect availability"]
