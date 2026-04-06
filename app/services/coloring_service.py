from typing import Any


class ColoringService:
    def color_graph(self, graph: dict[str, Any]) -> dict[str, Any]:
        for index, node in enumerate(graph.get("nodes", [])):
            node["color"] = "blue" if index % 2 == 0 else "green"
        return graph
