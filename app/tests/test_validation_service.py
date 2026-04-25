from app.services.validation_service import ValidationService


def sample_normalized_data() -> dict:
    return {
        "entities": {
            "employees": [
                {
                    "name": "Alice",
                    "skills": ["front_desk", "cert_a"],
                    "availability": ["monday", "tuesday"],
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
                    "start_time": "12:00",
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
    }


def test_detect_overlapping_employee_assignments() -> None:
    service = ValidationService()

    schedule_result = {
        "selected_assignments": [
            {
                "employee_name": "Alice",
                "shift_id": "shift_1",
                "day": "monday",
                "start_time": "09:00",
                "end_time": "13:00",
                "location": "apt_a",
            },
            {
                "employee_name": "Alice",
                "shift_id": "shift_2",
                "day": "monday",
                "start_time": "12:00",
                "end_time": "17:00",
                "location": "apt_b",
            },
        ]
    }

    result = service.validate(sample_normalized_data(), schedule_result)

    assert result["is_valid"] is False
    assert any(error["type"] == "employee_time_overlap" for error in result["errors"])


def test_detect_understaffed_shift() -> None:
    service = ValidationService()

    schedule_result = {
        "selected_assignments": [
            {
                "employee_name": "Alice",
                "shift_id": "shift_1",
                "day": "monday",
                "start_time": "09:00",
                "end_time": "13:00",
                "location": "apt_a",
            }
        ]
    }

    result = service.validate(sample_normalized_data(), schedule_result)

    assert result["is_valid"] is False
    assert any(error["type"] == "understaffed_shift" for error in result["errors"])


def test_valid_schedule_passes() -> None:
    service = ValidationService()

    normalized = {
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
    }

    schedule_result = {
        "selected_assignments": [
            {
                "employee_name": "Alice",
                "shift_id": "shift_1",
                "day": "monday",
                "start_time": "09:00",
                "end_time": "13:00",
                "location": "apt_a",
            },
            {
                "employee_name": "Bob",
                "shift_id": "shift_2",
                "day": "monday",
                "start_time": "13:00",
                "end_time": "17:00",
                "location": "apt_b",
            },
        ]
    }

    result = service.validate(normalized, schedule_result)

    assert result["is_valid"] is True
    assert result["error_count"] == 0


def test_normalized_shift_availability_passes() -> None:
    service = ValidationService()

    normalized = {
        "entities": {
            "employees": [
                {
                    "name": "Alice",
                    "skills": ["front_desk"],
                    "availability": ["monday_morning"],
                },
            ],
            "shifts": [
                {
                    "id": "shift_1",
                    "day": "monday",
                    "time": "morning",
                    "shift_label": "morning",
                    "location": "apt_a",
                    "required_skills": ["front_desk"],
                    "min_staff": 1,
                    "max_staff": 1,
                },
            ],
        },
        "constraints": {"hard_constraints": [], "soft_constraints": []},
    }
    schedule_result = {
        "selected_assignments": [
            {
                "employee_name": "Alice",
                "shift_id": "shift_1",
                "day": "monday",
                "start_time": "08:00",
                "end_time": "12:00",
                "location": "apt_a",
            }
        ]
    }

    result = service.validate(normalized, schedule_result)

    assert result["is_valid"] is True


def test_detect_max_shifts_violation() -> None:
    service = ValidationService()

    normalized = {
        "entities": {
            "employees": [
                {
                    "name": "Alice",
                    "skills": ["front_desk"],
                    "availability": ["monday"],
                    "max_shifts_per_week": 1,
                }
            ],
            "shifts": [
                {
                    "id": "shift_1",
                    "day": "monday",
                    "start_time": "09:00",
                    "end_time": "10:00",
                    "location": "apt_a",
                    "required_skills": ["front_desk"],
                    "min_staff": 1,
                    "max_staff": 1,
                },
                {
                    "id": "shift_2",
                    "day": "monday",
                    "start_time": "10:00",
                    "end_time": "11:00",
                    "location": "apt_b",
                    "required_skills": ["front_desk"],
                    "min_staff": 1,
                    "max_staff": 1,
                },
            ],
        },
        "constraints": {"hard_constraints": [], "soft_constraints": []},
    }
    schedule_result = {
        "selected_assignments": [
            {
                "employee_name": "Alice",
                "shift_id": "shift_1",
                "day": "monday",
                "start_time": "09:00",
                "end_time": "10:00",
                "location": "apt_a",
            },
            {
                "employee_name": "Alice",
                "shift_id": "shift_2",
                "day": "monday",
                "start_time": "10:00",
                "end_time": "11:00",
                "location": "apt_b",
            },
        ]
    }

    result = service.validate(normalized, schedule_result)

    assert result["is_valid"] is False
    assert any(error["type"] == "max_shifts_violation" for error in result["errors"])
