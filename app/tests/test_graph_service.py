from app.services.graph_service import GraphService


def test_graph_building() -> None:
    service = GraphService()
    graph = service.build_graph(["task A", "task B"])

    assert isinstance(graph, dict)
    assert len(graph["nodes"]) == 2
    assert graph["edges"] == []
