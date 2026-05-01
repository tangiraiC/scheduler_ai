from app.services.graph_serializer import serialize_graph
from app.services.graph_service import GraphService
from app.services.normalization_service import NormalizationService
from app.models.extraction import ExtractedConstraints


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


def test_normalization_preserves_cannot_work_pairs_and_edges() -> None:
    extracted = ExtractedConstraints.model_validate(
        {
            "job_type": "workforce_schedule",
            "entities": {
                "employees": [
                    {"name": "alice", "skills": ["front desk"], "availability": ["monday"]},
                    {"name": "bob", "skills": ["front desk"], "availability": ["monday"]},
                    {"name": "cara", "skills": ["front desk"], "availability": ["monday"]},
                ],
                "shifts": [
                    {
                        "id": "morning",
                        "day": "monday",
                        "time": "morning",
                        "required_skills": ["front desk"],
                    }
                ],
            },
            "constraints": {
                "hard_constraints": [],
                "soft_constraints": [],
                "cannot_work_with_pairs": [["alice", "bob"]],
            },
            "edges": [
                {"source": "bob", "target": "cara", "type": "cannot work with"},
            ],
        }
    )

    normalized = NormalizationService().normalize(extracted)

    assert normalized["constraints"]["cannot_work_with_pairs"] == [
        ["Alice", "Bob"],
        ["Bob", "Cara"],
    ]
    assert normalized["edges"] == [
        {"source": "Bob", "target": "Cara", "type": "cannot_work_with"}
    ]


def test_build_conflict_graph_uses_extracted_edges() -> None:
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
                    "max_staff": 2,
                }
            ],
        },
        "constraints": {"hard_constraints": [], "soft_constraints": []},
        "edges": [
            {"source": "Alice", "target": "Bob", "type": "cannot_work_with"},
        ],
    }

    result = service.build_conflict_graph(normalized_data)
    graph = result["graph"]

    assert graph["Alice__shift_1"]["Bob__shift_1"]["reason"] == "cannot_work_with"


def test_build_conflict_graph_matches_labeled_availability_to_explicit_time() -> None:
    service = GraphService()

    result = service.build_conflict_graph(
        {
            "entities": {
                "employees": [
                    {
                        "name": "Alice",
                        "skills": ["front_desk"],
                        "availability": ["monday_morning"],
                        "cannot_work_with": [],
                    }
                ],
                "shifts": [
                    {
                        "id": "shift_1",
                        "day": "monday",
                        "time": "09:00-13:00",
                        "shift_label": "",
                        "location": "clinic_a",
                        "required_skills": ["front_desk"],
                        "min_staff": 1,
                        "max_staff": 1,
                    }
                ],
            },
            "constraints": {"hard_constraints": [], "soft_constraints": []},
        }
    )

    assert result["node_count"] == 1
    assert result["nodes"][0]["node_id"] == "Alice__shift_1"


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
