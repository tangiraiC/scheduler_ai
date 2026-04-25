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
