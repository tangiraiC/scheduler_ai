from app.services.graph_serializer import serialize_graph
from app.services.graph_service import GraphService


def test_legacy_graph_building() -> None:
    service = GraphService()
    graph = service.build_graph(["task A", "task B"])

    assert isinstance(graph, dict)
    assert len(graph["nodes"]) == 2
    assert graph["edges"] == []


def test_build_conflict_graph_with_explicit_times() -> None:
    service = GraphService()

    normalized_data = {
        "entities": {
            "employees": [
                {
                    "name": "Alice",
                    "skills": ["cert_a", "front_desk"],
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
                    "end_time": "17:00",
                    "location": "apt_a",
                    "required_skills": ["front_desk"],
                    "min_staff": 1,
                    "max_staff": 1,
                },
                {
                    "id": "shift_2",
                    "day": "monday",
                    "start_time": "13:00",
                    "end_time": "21:00",
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

    result = service.build_conflict_graph(normalized_data)
    graph = result["graph"]

    assert graph.number_of_nodes() == 4
    assert graph.has_edge("Alice__shift_1", "Alice__shift_2")
    # Candidates for the same shift no longer inherently conflict (multi-staff supported)
    assert not graph.has_edge("Alice__shift_1", "Bob__shift_1")
    assert not graph.has_edge("Alice__shift_2", "Bob__shift_2")


def test_build_conflict_graph_with_normalized_shift_labels() -> None:
    service = GraphService()

    normalized_data = {
        "entities": {
            "employees": [
                {
                    "name": "Alice",
                    "skills": ["front_desk"],
                    "availability": ["monday_morning"],
                    "cannot_work_with": [],
                },
                {
                    "name": "Bob",
                    "skills": ["front_desk"],
                    "availability": ["monday_morning"],
                    "cannot_work_with": ["Alice"],
                },
                {
                    "name": "Cara",
                    "skills": ["inventory"],
                    "availability": ["monday_morning"],
                    "cannot_work_with": [],
                },
            ],
            "shifts": [
                {
                    "id": "shift_1",
                    "day": "monday",
                    "time": "morning",
                    "shift_label": "morning",
                    "location": "clinic_a",
                    "required_skills": ["front_desk"],
                    "min_staff": 1,
                    "max_staff": 1,
                },
                {
                    "id": "shift_2",
                    "day": "tuesday",
                    "time": "morning",
                    "shift_label": "morning",
                    "location": "clinic_a",
                    "required_skills": ["front_desk"],
                    "min_staff": 1,
                    "max_staff": 1,
                },
            ],
        },
        "constraints": {"hard_constraints": [], "soft_constraints": []},
    }

    result = service.build_conflict_graph(normalized_data)
    graph = result["graph"]

    assert graph.number_of_nodes() == 2
    assert "Cara__shift_1" not in graph.nodes
    assert "Alice__shift_2" not in graph.nodes
    # Since Bob cannot work with Alice, and they are both scheduled for the same time on shift_1:
    assert graph["Alice__shift_1"]["Bob__shift_1"]["reason"] == "cannot_work_with"


def test_serialize_graph() -> None:
    service = GraphService()
    result = service.build_conflict_graph(
        {
            "entities": {
                "employees": [
                    {
                        "name": "Alice",
                        "skills": ["front_desk"],
                        "availability": ["monday"],
                    }
                ],
                "shifts": [
                    {
                        "id": "shift_1",
                        "day": "monday",
                        "start_time": "09:00",
                        "end_time": "17:00",
                        "required_skills": ["front_desk"],
                    }
                ],
            },
            "constraints": {},
        }
    )

    serialized = serialize_graph(result["graph"])

    assert serialized["meta"] == {"node_count": 1, "edge_count": 0}
    assert serialized["nodes"][0]["id"] == "Alice__shift_1"
    assert serialized["edges"] == []
