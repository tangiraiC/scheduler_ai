from app.services.extraction_service import extract_constraints


def test_extraction():
    text = """
    There are front desk attendants. Some require certification.
    Some cannot work weekends. Max 40 hours per week.
    Shifts are 8 hours.
    """

    result = extract_constraints(text)

    assert result.planning_horizon_days == 7
    assert result.hard_constraints.max_hours_per_7_days == 40