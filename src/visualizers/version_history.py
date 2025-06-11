"""
Version history visualization module.
Provides visualization tools for library version history.
"""

import logging
import re
from typing import Any, Optional

from pydantic import BaseModel, Field

from ..organizers.library_version_tracker import LibraryRegistry, LibraryVersionTracker

logger = logging.getLogger(__name__)


class VersionNode(BaseModel):
    """Model for a version node in the visualization."""

    version: str
    timestamp: Optional[str] = None
    doc_count: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class VersionEdge(BaseModel):
    """Model for a version edge in the visualization."""

    source: str
    target: str
    added: int = 0
    removed: int = 0
    modified: int = 0
    metadata: dict[str, Any] = Field(default_factory=dict)


class VersionGraph(BaseModel):
    """Model for a version graph."""

    library_name: str
    nodes: list[VersionNode] = Field(default_factory=list)
    edges: list[VersionEdge] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class VersionHistoryVisualizer:
    """
    Visualizer for library version history.
    Provides tools for visualizing version history and differences.
    """

    def __init__(
        self,
        tracker: Optional[LibraryVersionTracker] = None,
        registry: Optional[LibraryRegistry] = None,
    ):
        """
        Initialize the visualizer.

        Args:
            tracker: Optional version tracker
            registry: Optional library registry
        """
        self.tracker = tracker
        self.registry = registry

        if registry and not tracker:
            self.tracker = LibraryVersionTracker(registry)

        if not registry and tracker:
            self.registry = tracker.registry

    def create_version_graph(self, library_name: str) -> VersionGraph:
        """
        Create a version graph for a library.

        Args:
            library_name: Name of the library

        Returns:
            VersionGraph object
        """
        if not self.registry:
            raise ValueError("Registry is required to create a version graph")

        library = self.registry.get_library(library_name)
        if not library:
            raise ValueError(f"Library {library_name} not found in registry")

        # Create graph
        graph = VersionGraph(library_name=library_name)

        # Add nodes
        versions = list(library.get("versions", {}).keys())
        versions.sort(key=self._version_sort_key)

        for version in versions:
            version_data = library["versions"][version]
            doc_count = len(version_data.get("documents", []))

            node = VersionNode(
                version=version,
                timestamp=version_data.get("timestamp"),
                doc_count=doc_count,
                metadata={"url": version_data.get("url")},
            )

            graph.nodes.append(node)

        # Add edges
        for i in range(len(versions) - 1):
            v1 = versions[i]
            v2 = versions[i + 1]

            # Get diff
            diff = self.tracker.compare_versions(library_name, v1, v2)

            edge = VersionEdge(
                source=v1,
                target=v2,
                added=len(diff.added_pages),
                removed=len(diff.removed_pages),
                modified=len(diff.modified_pages),
                metadata={"diff_id": f"{library_name}_{v1}_vs_{v2}"},
            )

            graph.edges.append(edge)

        return graph

    def generate_html_visualization(
        self, graph: VersionGraph, output_file: str
    ) -> None:
        """
        Generate an HTML visualization of a version graph.

        Args:
            graph: Version graph to visualize
            output_file: Path to output HTML file
        """
        # Convert graph to JSON for JavaScript
        graph_json = graph.model_dump_json()

        # Create HTML
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{graph.library_name} Version History</title>
            <script src="https://d3js.org/d3.v7.min.js"></script>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    margin: 0;
                    padding: 20px;
                }}

                h1 {{
                    text-align: center;
                }}

                #graph {{
                    width: 100%;
                    height: 600px;
                    border: 1px solid #ccc;
                    border-radius: 5px;
                }}

                .node {{
                    cursor: pointer;
                }}

                .node circle {{
                    fill: #69b3a2;
                    stroke: #fff;
                    stroke-width: 2px;
                }}

                .node text {{
                    font-size: 12px;
                }}

                .link {{
                    fill: none;
                    stroke: #ccc;
                    stroke-width: 2px;
                }}

                .tooltip {{
                    position: absolute;
                    background-color: white;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 10px;
                    pointer-events: none;
                    opacity: 0;
                    transition: opacity 0.3s;
                }}
            </style>
        </head>
        <body>
            <h1>{graph.library_name} Version History</h1>
            <div id="graph"></div>

            <script>
                // Graph data
                const graphData = {graph_json};

                // Create visualization
                const width = document.getElementById('graph').clientWidth;
                const height = document.getElementById('graph').clientHeight;

                // Create SVG
                const svg = d3.select('#graph')
                    .append('svg')
                    .attr('width', width)
                    .attr('height', height);

                // Create tooltip
                const tooltip = d3.select('body')
                    .append('div')
                    .attr('class', 'tooltip');

                // Create simulation
                const simulation = d3.forceSimulation()
                    .force('link', d3.forceLink().id(d => d.version).distance(150))
                    .force('charge', d3.forceManyBody().strength(-300))
                    .force('center', d3.forceCenter(width / 2, height / 2));

                // Create links
                const link = svg.append('g')
                    .selectAll('line')
                    .data(graphData.edges)
                    .enter()
                    .append('line')
                    .attr('class', 'link')
                    .attr('stroke-width', d => Math.sqrt(d.added + d.removed + d.modified))
                    .on('mouseover', function(event, d) {{
                        tooltip.transition()
                            .duration(200)
                            .style('opacity', 0.9);
                        tooltip.html(`
                            <strong>Changes from ${{d.source}} to ${{d.target}}:</strong><br>
                            Added: ${{d.added}}<br>
                            Removed: ${{d.removed}}<br>
                            Modified: ${{d.modified}}
                        `)
                            .style('left', (event.pageX + 10) + 'px')
                            .style('top', (event.pageY - 28) + 'px');
                    }})
                    .on('mouseout', function() {{
                        tooltip.transition()
                            .duration(500)
                            .style('opacity', 0);
                    }});

                // Create nodes
                const node = svg.append('g')
                    .selectAll('.node')
                    .data(graphData.nodes)
                    .enter()
                    .append('g')
                    .attr('class', 'node')
                    .on('mouseover', function(event, d) {{
                        tooltip.transition()
                            .duration(200)
                            .style('opacity', 0.9);
                        tooltip.html(`
                            <strong>Version: ${{d.version}}</strong><br>
                            Documents: ${{d.doc_count}}<br>
                            ${{d.timestamp ? 'Date: ' + new Date(d.timestamp).toLocaleDateString() : ''}}
                        `)
                            .style('left', (event.pageX + 10) + 'px')
                            .style('top', (event.pageY - 28) + 'px');
                    }})
                    .on('mouseout', function() {{
                        tooltip.transition()
                            .duration(500)
                            .style('opacity', 0);
                    }})
                    .call(d3.drag()
                        .on('start', dragstarted)
                        .on('drag', dragged)
                        .on('end', dragended));

                // Add circles to nodes
                node.append('circle')
                    .attr('r', d => 10 + Math.sqrt(d.doc_count))
                    .attr('fill', '#69b3a2');

                // Add text to nodes
                node.append('text')
                    .attr('dx', 12)
                    .attr('dy', '.35em')
                    .text(d => d.version);

                // Update simulation
                simulation
                    .nodes(graphData.nodes)
                    .on('tick', ticked);

                simulation.force('link')
                    .links(graphData.edges);

                // Tick function
                function ticked() {{
                    link
                        .attr('x1', d => d.source.x)
                        .attr('y1', d => d.source.y)
                        .attr('x2', d => d.target.x)
                        .attr('y2', d => d.target.y);

                    node
                        .attr('transform', d => `translate(${{d.x}},${{d.y}})`);
                }}

                // Drag functions
                function dragstarted(event, d) {{
                    if (!event.active) simulation.alphaTarget(0.3).restart();
                    d.fx = d.x;
                    d.fy = d.y;
                }}

                function dragged(event, d) {{
                    d.fx = event.x;
                    d.fy = event.y;
                }}

                function dragended(event, d) {{
                    if (!event.active) simulation.alphaTarget(0);
                    d.fx = null;
                    d.fy = null;
                }}
            </script>
        </body>
        </html>
        """

        # Write HTML to file
        with open(output_file, "w") as f:
            f.write(html)

        logger.info(f"Version history visualization saved to {output_file}")

    def _version_sort_key(self, version: str) -> tuple:
        """
        Create a sort key for version strings.

        Args:
            version: Version string

        Returns:
            Tuple for sorting
        """
        # Extract components from version string
        components = []
        for part in re.split(r"[.-]", version):
            try:
                components.append(int(part))
            except ValueError:
                components.append(part)

        return tuple(components)
