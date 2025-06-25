#!/usr/bin/env python3
"""
Dependency Graph Generator for Multi-Library Documentation

Creates visual dependency graphs and relationship diagrams.
"""

import json
from typing import Any, Optional


class DependencyGraphGenerator:
    """Generator for creating dependency relationship graphs."""

    def __init__(self):
        """Initialize the dependency graph generator."""
        self.graph_data = {}

    def create_graph(self, dependencies: list[dict[str, Any]]) -> "DependencyGraph":
        """
        Create a dependency graph from a list of dependencies.

        Args:
            dependencies: List of dependency dictionaries

        Returns:
            DependencyGraph object
        """
        graph = DependencyGraph()

        # Add nodes for each dependency
        for dependency in dependencies:
            node_id = dependency["name"]
            node_data = {
                "name": dependency["name"],
                "version": dependency.get("version", ""),
                "type": dependency.get("type", "unknown"),
                "dev": dependency.get("dev", False),
                "source": dependency.get("source", "unknown"),
            }
            graph.add_node(node_id, node_data)

        # Add edges based on relationships (if available)
        for dependency in dependencies:
            if "parent" in dependency:
                parent_id = dependency["parent"]
                child_id = dependency["name"]
                graph.add_edge(parent_id, child_id, {"relationship": "depends_on"})

        return graph

    def generate_html_visualization(self, graph: "DependencyGraph") -> str:
        """
        Generate HTML visualization of the dependency graph.

        Args:
            graph: DependencyGraph object

        Returns:
            HTML string for visualization
        """
        nodes_json = json.dumps(
            [
                {
                    "id": node_id,
                    "label": data["name"],
                    "type": data["type"],
                    "dev": data.get("dev", False),
                    "version": data.get("version", ""),
                }
                for node_id, data in graph.nodes.items()
            ]
        )

        edges_json = json.dumps(
            [
                {
                    "from": edge["from"],
                    "to": edge["to"],
                    "relationship": edge["data"].get("relationship", "unknown"),
                }
                for edge in graph.edges
            ]
        )

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Dependency Graph</title>
            <script src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
            <style>
                #dependency-graph {{
                    width: 100%;
                    height: 600px;
                    border: 1px solid #ccc;
                }}
                .legend {{
                    margin: 10px 0;
                    padding: 10px;
                    background: #f5f5f5;
                    border-radius: 5px;
                }}
            </style>
        </head>
        <body>
            <h2>Project Dependency Graph</h2>
            <div class="legend">
                <strong>Legend:</strong>
                <span style="color: #4CAF50;">● Production Dependencies</span>
                <span style="color: #FF9800;">● Development Dependencies</span>
            </div>
            <div id="dependency-graph"></div>

            <script>
                const nodes = new vis.DataSet({nodes_json});
                const edges = new vis.DataSet({edges_json});

                // Color nodes based on type and dev status
                nodes.forEach(function(node) {{
                    if (node.dev) {{
                        node.color = '#FF9800'; // Orange for dev dependencies
                    }} else {{
                        node.color = '#4CAF50'; // Green for production dependencies
                    }}
                    node.title = `${{node.label}} (${{node.type}}) - ${{node.version}}`;
                }});

                const container = document.getElementById('dependency-graph');
                const data = {{ nodes: nodes, edges: edges }};
                const options = {{
                    nodes: {{
                        shape: 'dot',
                        size: 16,
                        font: {{ size: 12 }}
                    }},
                    edges: {{
                        arrows: 'to',
                        color: '#848484'
                    }},
                    physics: {{
                        stabilization: false,
                        barnesHut: {{
                            gravitationalConstant: -2000,
                            springConstant: 0.001,
                            springLength: 200
                        }}
                    }}
                }};

                const network = new vis.Network(container, data, options);
            </script>
        </body>
        </html>
        """

        return html


class DependencyGraph:
    """Represents a dependency graph with nodes and edges."""

    def __init__(self):
        """Initialize an empty dependency graph."""
        self.nodes = {}
        self.edges = []

    def add_node(self, node_id: str, data: dict[str, Any]):
        """
        Add a node to the graph.

        Args:
            node_id: Unique identifier for the node
            data: Node data dictionary
        """
        self.nodes[node_id] = data

    def add_edge(
        self, from_node: str, to_node: str, data: Optional[dict[str, Any]] = None
    ):
        """
        Add an edge between two nodes.

        Args:
            from_node: Source node ID
            to_node: Target node ID
            data: Optional edge data
        """
        edge = {"from": from_node, "to": to_node, "data": data or {}}
        self.edges.append(edge)

    def get_node_count(self) -> int:
        """Get the number of nodes in the graph."""
        return len(self.nodes)

    def get_edge_count(self) -> int:
        """Get the number of edges in the graph."""
        return len(self.edges)

    def to_dict(self) -> dict[str, Any]:
        """Convert graph to dictionary representation."""
        return {
            "nodes": self.nodes,
            "edges": self.edges,
            "metadata": {
                "node_count": self.get_node_count(),
                "edge_count": self.get_edge_count(),
            },
        }
