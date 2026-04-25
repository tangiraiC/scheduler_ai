from app.services.solver_service import SolverService


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
                {
                    "name": "Carol",
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
                {
                    "id": "shift_3",
                    "day": "tuesday",
                    "start_time": "09:00",
                    "end_time": "17:00",
                    "location": "apt_c",
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


def test_greedy_color_largest_first() -> None:
    service = SolverService()
    result = service.solve(sample_normalized_data(), strategy="largest_first")

    assert "coloring" in result
    assert "schedule" in result
    assert "nodes" in result
    assert result["node_count"] > 0
    assert result["color_count"] >= 1


def test_compare_strategies() -> None:
    service = SolverService()
    result = service.compare_strategies(
        sample_normalized_data(),
        strategies=["largest_first", "saturation_largest_first"],
    )

    assert "results" in result
    assert len(result["results"]) >= 1
    assert result["best_strategy"] in ["largest_first", "saturation_largest_first"]


def test_selected_schedule_has_one_assignment_per_shift() -> None:
    service = SolverService()
    result = service.solve(sample_normalized_data(), strategy="largest_first")

    selected = result["selected_assignments"]
    shift_ids = [item["shift_id"] for item in selected]

    assert len(shift_ids) == len(set(shift_ids))


def test_selected_assignments_do_not_conflict() -> None:
    service = SolverService()
    result = service.solve(sample_normalized_data(), strategy="largest_first")

    selected_node_ids = {item["node_id"] for item in result["selected_assignments"]}
    selected_edges = [
        edge
        for edge in result["edges"]
        if edge["source"] in selected_node_ids and edge["target"] in selected_node_ids
    ]

    assert selected_edges == []


def test_solve_returns_candidate_without_validation_result() -> None:
    service = SolverService()
    result = service.solve(sample_normalized_data(), strategy="largest_first")

    assert "validation" not in result
    assert "selected_assignments" in result


def test_solver_balances_assignments_across_feasible_employees() -> None:
    service = SolverService()
    result = service.solve(sample_normalized_data(), strategy="largest_first")

    employee_names = [item["employee_name"] for item in result["selected_assignments"]]

    assert len(set(employee_names)) > 1


def test_solver_respects_employee_max_shifts() -> None:
    service = SolverService()
    normalized_data = {
        "entities": {
            "employees": [
                {
                    "name": "Alice",
                    "skills": ["front_desk"],
                    "availability": ["monday"],
                    "max_shifts_per_week": 1,
                },
                {
                    "name": "Bob",
                    "skills": ["front_desk"],
                    "availability": ["monday"],
                    "max_shifts_per_week": 5,
                },
            ],
            "shifts": [
                {
                    "id": "shift_1",
                    "day": "monday",
                    "start_time": "09:00",
                    "end_time": "10:00",
                    "required_skills": ["front_desk"],
                    "min_staff": 1,
                    "max_staff": 1,
                },
                {
                    "id": "shift_2",
                    "day": "monday",
                    "start_time": "10:00",
                    "end_time": "11:00",
                    "required_skills": ["front_desk"],
                    "min_staff": 1,
                    "max_staff": 1,
                },
            ],
        },
        "constraints": {"hard_constraints": [], "soft_constraints": []},
    }

    result = service.solve(normalized_data, strategy="largest_first")
    alice_assignments = [
        item for item in result["selected_assignments"] if item["employee_name"] == "Alice"
    ]

    assert len(alice_assignments) <= 1
