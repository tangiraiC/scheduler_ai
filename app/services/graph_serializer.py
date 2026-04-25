from __future__ import annotations

from typing import Any

import networkx as nx


def serialize_graph(graph: nx.Graph) -> dict[str, Any]:
    return {
        "nodes": [
            {
                "id": node_id,
                **attrs,
            }
            for node_id, attrs in graph.nodes(data=True)
        ],
        "edges": [
            {
                "source": source,
                "target": target,
                **attrs,
            }
            for source, target, attrs in graph.edges(data=True)
        ],
        "meta": {
            "node_count": graph.number_of_nodes(),
            "edge_count": graph.number_of_edges(),
        },
    }
