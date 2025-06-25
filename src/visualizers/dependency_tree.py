#!/usr/bin/env python3
"""
Dependency Tree Visualizer for Multi-Library Documentation

Creates visual dependency trees and hierarchical representations.
"""

import json
from typing import Any


class DependencyTreeVisualizer:
    """Visualizer for creating dependency tree representations."""

    def __init__(self):
        """Initialize the dependency tree visualizer."""
        self.tree_styles = {
            "default": {
                "node_color": "#4CAF50",
                "dev_node_color": "#FF9800",
                "edge_color": "#757575",
                "font_family": "Arial, sans-serif",
            },
            "dark": {
                "node_color": "#66BB6A",
                "dev_node_color": "#FFB74D",
                "edge_color": "#BDBDBD",
                "font_family": "Arial, sans-serif",
            },
        }

    def generate_tree_html(
        self, dependencies: list[dict[str, Any]], style: str = "default"
    ) -> str:
        """
        Generate HTML visualization of dependency tree.

        Args:
            dependencies: List of dependency dictionaries
            style: Visual style ('default' or 'dark')

        Returns:
            HTML string for tree visualization
        """
        tree_data = self._build_tree_structure(dependencies)
        style_config = self.tree_styles.get(style, self.tree_styles["default"])

        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Dependency Tree</title>
            <style>
                body {{
                    font-family: {style_config['font_family']};
                    margin: 20px;
                    background-color: {'#1e1e1e' if style == 'dark' else '#ffffff'};
                    color: {'#ffffff' if style == 'dark' else '#000000'};
                }}
                .dependency-tree {{
                    margin: 20px 0;
                }}
                .tree-node {{
                    margin: 5px 0;
                    padding: 8px 12px;
                    border-radius: 4px;
                    display: inline-block;
                    min-width: 200px;
                }}
                .production-dep {{
                    background-color: {style_config['node_color']};
                    color: white;
                }}
                .dev-dep {{
                    background-color: {style_config['dev_node_color']};
                    color: white;
                }}
                .tree-level {{
                    margin-left: 30px;
                    border-left: 2px solid {style_config['edge_color']};
                    padding-left: 15px;
                }}
                .tree-connector {{
                    color: {style_config['edge_color']};
                    margin-right: 10px;
                }}
                .dependency-info {{
                    font-size: 0.9em;
                    opacity: 0.8;
                }}
                .legend {{
                    margin: 20px 0;
                    padding: 15px;
                    background-color: {'#2d2d2d' if style == 'dark' else '#f5f5f5'};
                    border-radius: 5px;
                }}
                .legend-item {{
                    display: inline-block;
                    margin-right: 20px;
                    margin-bottom: 5px;
                }}
                .legend-color {{
                    display: inline-block;
                    width: 20px;
                    height: 20px;
                    border-radius: 3px;
                    margin-right: 8px;
                    vertical-align: middle;
                }}
            </style>
        </head>
        <body>
            <h2>Project Dependency Tree</h2>

            <div class="legend">
                <h3>Legend</h3>
                <div class="legend-item">
                    <span class="legend-color" style="background-color: {style_config['node_color']};"></span>
                    Production Dependencies
                </div>
                <div class="legend-item">
                    <span class="legend-color" style="background-color: {style_config['dev_node_color']};"></span>
                    Development Dependencies
                </div>
            </div>

            <div class="dependency-tree">
                {self._render_tree_html(tree_data)}
            </div>

            <div style="margin-top: 30px;">
                <h3>Summary</h3>
                <p>Total Dependencies: {len(dependencies)}</p>
                <p>Production: {len([d for d in dependencies if not d.get('dev', False)])}</p>
                <p>Development: {len([d for d in dependencies if d.get('dev', False)])}</p>
            </div>
        </body>
        </html>
        """

        return html

    def generate_tree_ascii(self, dependencies: list[dict[str, Any]]) -> str:
        """
        Generate ASCII art representation of dependency tree.

        Args:
            dependencies: List of dependency dictionaries

        Returns:
            ASCII tree string
        """
        tree_data = self._build_tree_structure(dependencies)
        return self._render_tree_ascii(tree_data)

    def generate_tree_json(self, dependencies: list[dict[str, Any]]) -> str:
        """
        Generate JSON representation of dependency tree.

        Args:
            dependencies: List of dependency dictionaries

        Returns:
            JSON string of tree structure
        """
        tree_data = self._build_tree_structure(dependencies)
        return json.dumps(tree_data, indent=2)

    def _build_tree_structure(
        self, dependencies: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Build hierarchical tree structure from flat dependency list."""
        # Group dependencies by parent
        by_parent = {"root": []}

        for dep in dependencies:
            parent = dep.get("parent", "root")
            if parent not in by_parent:
                by_parent[parent] = []
            by_parent[parent].append(dep)

        # Build tree recursively
        def build_node(parent_name: str) -> dict[str, Any]:
            children = by_parent.get(parent_name, [])
            node = {"name": parent_name, "children": []}

            for child_dep in children:
                child_name = child_dep["name"]
                child_node = {
                    "name": child_name,
                    "version": child_dep.get("version", ""),
                    "type": child_dep.get("type", "unknown"),
                    "dev": child_dep.get("dev", False),
                    "source": child_dep.get("source", "unknown"),
                    "children": [],
                }

                # Recursively add children
                if child_name in by_parent:
                    child_node["children"] = [
                        build_node(grandchild["name"])
                        for grandchild in by_parent[child_name]
                    ]

                node["children"].append(child_node)

            return node

        return build_node("root")

    def _render_tree_html(self, tree_node: dict[str, Any], level: int = 0) -> str:
        """Render tree structure as HTML."""
        html = ""

        if tree_node["name"] != "root":
            dep_class = "dev-dep" if tree_node.get("dev", False) else "production-dep"
            version = tree_node.get("version", "")
            dep_type = tree_node.get("type", "")

            connector = "├── " if level > 0 else ""

            html += f"""
            <div class="tree-level">
                <div class="tree-node {dep_class}">
                    <span class="tree-connector">{connector}</span>
                    <strong>{tree_node['name']}</strong>
                    <div class="dependency-info">
                        Version: {version} | Type: {dep_type}
                    </div>
                </div>
            """

        # Render children
        for child in tree_node.get("children", []):
            html += self._render_tree_html(child, level + 1)

        if tree_node["name"] != "root":
            html += "</div>"

        return html

    def _render_tree_ascii(
        self, tree_node: dict[str, Any], prefix: str = "", is_last: bool = True
    ) -> str:
        """Render tree structure as ASCII art."""
        result = ""

        if tree_node["name"] != "root":
            connector = "└── " if is_last else "├── "
            version = tree_node.get("version", "")
            dev_marker = " [DEV]" if tree_node.get("dev", False) else ""

            result += f"{prefix}{connector}{tree_node['name']} {version}{dev_marker}\n"

            # Update prefix for children
            child_prefix = prefix + ("    " if is_last else "│   ")
        else:
            child_prefix = prefix

        # Render children
        children = tree_node.get("children", [])
        for i, child in enumerate(children):
            is_last_child = i == len(children) - 1
            result += self._render_tree_ascii(child, child_prefix, is_last_child)

        return result

    def generate_mermaid_diagram(self, dependencies: list[dict[str, Any]]) -> str:
        """
        Generate Mermaid diagram syntax for dependency tree.

        Args:
            dependencies: List of dependency dictionaries

        Returns:
            Mermaid diagram syntax string
        """
        mermaid = "graph TD\n"

        # Add nodes
        for dep in dependencies:
            name = dep["name"]
            version = dep.get("version", "")
            dev_marker = "[DEV]" if dep.get("dev", False) else ""

            # Clean name for Mermaid (replace special characters)
            clean_name = name.replace("-", "_").replace(".", "_")
            display_name = f"{name} {version} {dev_marker}".strip()

            mermaid += f'    {clean_name}["{display_name}"]\n'

        # Add edges (relationships)
        for dep in dependencies:
            if "parent" in dep:
                parent_clean = dep["parent"].replace("-", "_").replace(".", "_")
                child_clean = dep["name"].replace("-", "_").replace(".", "_")
                mermaid += f"    {parent_clean} --> {child_clean}\n"

        # Add styling
        mermaid += "\n    classDef prodDep fill:#4CAF50,stroke:#333,stroke-width:2px,color:#fff\n"
        mermaid += (
            "    classDef devDep fill:#FF9800,stroke:#333,stroke-width:2px,color:#fff\n"
        )

        # Apply styles
        for dep in dependencies:
            clean_name = dep["name"].replace("-", "_").replace(".", "_")
            style_class = "devDep" if dep.get("dev", False) else "prodDep"
            mermaid += f"    class {clean_name} {style_class}\n"

        return mermaid

    def analyze_tree_metrics(
        self, dependencies: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Analyze dependency tree metrics.

        Args:
            dependencies: List of dependency dictionaries

        Returns:
            Dictionary with tree metrics
        """
        tree_data = self._build_tree_structure(dependencies)

        def calculate_depth(node: dict[str, Any]) -> int:
            if not node.get("children"):
                return 0
            return 1 + max(calculate_depth(child) for child in node["children"])

        def count_nodes(node: dict[str, Any]) -> int:
            count = 1 if node["name"] != "root" else 0
            for child in node.get("children", []):
                count += count_nodes(child)
            return count

        total_deps = len(dependencies)
        prod_deps = len([d for d in dependencies if not d.get("dev", False)])
        dev_deps = len([d for d in dependencies if d.get("dev", False)])

        # Group by type
        by_type = {}
        for dep in dependencies:
            dep_type = dep.get("type", "unknown")
            by_type[dep_type] = by_type.get(dep_type, 0) + 1

        metrics = {
            "total_dependencies": total_deps,
            "production_dependencies": prod_deps,
            "development_dependencies": dev_deps,
            "max_depth": calculate_depth(tree_data),
            "dependencies_by_type": by_type,
            "has_circular_dependencies": self._detect_circular_dependencies(
                dependencies
            ),
            "complexity_score": self._calculate_complexity_score(dependencies),
        }

        return metrics

    def _detect_circular_dependencies(self, dependencies: list[dict[str, Any]]) -> bool:
        """Detect if there are circular dependencies."""
        # Build adjacency list
        graph = {}
        for dep in dependencies:
            name = dep["name"]
            parent = dep.get("parent")

            if parent:
                if parent not in graph:
                    graph[parent] = []
                graph[parent].append(name)

        # DFS to detect cycles
        visited = set()
        rec_stack = set()

        def has_cycle(node: str) -> bool:
            if node in rec_stack:
                return True
            if node in visited:
                return False

            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph.get(node, []):
                if has_cycle(neighbor):
                    return True

            rec_stack.remove(node)
            return False

        for node in graph:
            if node not in visited:
                if has_cycle(node):
                    return True

        return False

    def _calculate_complexity_score(self, dependencies: list[dict[str, Any]]) -> float:
        """Calculate complexity score based on dependency structure."""
        if not dependencies:
            return 0.0

        total_deps = len(dependencies)
        unique_types = len(set(dep.get("type", "unknown") for dep in dependencies))
        has_dev_deps = any(dep.get("dev", False) for dep in dependencies)

        # Base complexity from number of dependencies
        complexity = min(total_deps / 10.0, 1.0)

        # Add complexity for multiple ecosystems
        complexity += (unique_types - 1) * 0.1

        # Add complexity for dev dependencies
        if has_dev_deps:
            complexity += 0.1

        return min(complexity, 1.0)
