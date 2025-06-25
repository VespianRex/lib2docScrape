"""
Visualizations for lib2docScrape.
"""

import json
import logging
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class VisualizationConfig(BaseModel):
    """Configuration for visualizations."""

    enable_charts: bool = True
    enable_graphs: bool = True
    enable_maps: bool = True
    enable_tables: bool = True
    enable_export: bool = True
    default_chart_type: str = "bar"
    default_color_scheme: str = "category10"
    max_items_per_chart: int = 100
    chart_width: int = 800
    chart_height: int = 400
    animation_duration: int = 500
    custom_css: Optional[str] = None
    custom_js: Optional[str] = None


class Visualizations:
    """
    Visualizations for lib2docScrape.
    Provides interactive visualizations for documentation data.
    """

    def __init__(self, app: FastAPI, config: Optional[VisualizationConfig] = None):
        """
        Initialize the visualizations.

        Args:
            app: FastAPI application
            config: Optional visualization configuration
        """
        self.app = app
        self.config = config or VisualizationConfig()

        # Set up routes
        self._setup_routes()

        logger.info(
            f"Visualizations initialized with default_chart_type={self.config.default_chart_type}"
        )

    def _setup_routes(self) -> None:
        """Set up visualization routes."""

        # Chart API
        @self.app.get("/api/visualizations/chart")
        async def get_chart(
            type: str = None,
            data: str = None,  # Type hint for data will be List[Dict[str, Any]] after json.loads
            options: str = None,  # Type hint for options will be Dict[str, Any] after json.loads
        ):
            # Validate chart type
            chart_type = type or self.config.default_chart_type
            if chart_type not in ["bar", "line", "pie", "scatter", "area", "heatmap"]:
                raise HTTPException(
                    status_code=400, detail=f"Invalid chart type: {chart_type}"
                )

            # Parse data
            chart_data_parsed = []
            if data:
                try:
                    chart_data_parsed = json.loads(data)
                except json.JSONDecodeError as e:
                    raise HTTPException(
                        status_code=400, detail="Invalid data format"
                    ) from e

            # Parse options
            chart_options_parsed = {}
            if options:
                try:
                    chart_options_parsed = json.loads(options)
                except json.JSONDecodeError as e:
                    raise HTTPException(
                        status_code=400, detail="Invalid options format"
                    ) from e

            # Generate chart configuration
            chart_config = self._generate_chart_config(
                chart_type, chart_data_parsed, chart_options_parsed
            )

            return chart_config

        # Graph API
        @self.app.get("/api/visualizations/graph")
        async def get_graph(
            data: str = None,  # Type hint for data will be Dict[str, List[Dict[str, Any]]] after json.loads
            options: str = None,  # Type hint for options will be Dict[str, Any] after json.loads
        ):
            if not self.config.enable_graphs:
                raise HTTPException(status_code=403, detail="Graphs are disabled")

            # Parse data
            graph_data_parsed = {"nodes": [], "links": []}
            if data:
                try:
                    graph_data_parsed = json.loads(data)
                except json.JSONDecodeError as e:
                    raise HTTPException(
                        status_code=400, detail="Invalid data format"
                    ) from e

            # Parse options
            graph_options_parsed = {}
            if options:
                try:
                    graph_options_parsed = json.loads(options)
                except json.JSONDecodeError as e:
                    raise HTTPException(
                        status_code=400, detail="Invalid options format"
                    ) from e

            # Generate graph configuration
            graph_config = self._generate_graph_config(
                graph_data_parsed, graph_options_parsed
            )

            return graph_config

        # Table API
        @self.app.get("/api/visualizations/table")
        async def get_table(
            data: str = None,  # Type hint for data will be List[Dict[str, Any]] after json.loads
            options: str = None,  # Type hint for options will be Dict[str, Any] after json.loads
        ):
            if not self.config.enable_tables:
                raise HTTPException(status_code=403, detail="Tables are disabled")

            # Parse data
            table_data_parsed = []
            if data:
                try:
                    table_data_parsed = json.loads(data)
                except json.JSONDecodeError as e:
                    raise HTTPException(
                        status_code=400, detail="Invalid data format"
                    ) from e

            # Parse options
            table_options_parsed = {}
            if options:
                try:
                    table_options_parsed = json.loads(options)
                except json.JSONDecodeError as e:
                    raise HTTPException(
                        status_code=400, detail="Invalid options format"
                    ) from e

            # Generate table configuration
            table_config = self._generate_table_config(
                table_data_parsed, table_options_parsed
            )

            return table_config

        # Export routes
        @self.app.get("/export/csv")
        async def export_csv():
            """Export data as CSV."""
            from fastapi.responses import Response

            csv_data = "header1,header2\nvalue1,value2\n"
            return Response(
                content=csv_data,
                media_type="text/csv",
                headers={"Content-Disposition": "attachment; filename=export.csv"},
            )

    def _generate_chart_config(
        self, chart_type: str, data: list, options: dict
    ) -> dict:  # Adjusted type hints
        """
        Generate chart configuration.

        Args:
            chart_type: Chart type
            data: Chart data (List[Dict[str, Any]])
            options: Chart options (Dict[str, Any])

        Returns:
            Chart configuration
        """
        # Base configuration
        chart_config = {
            "type": chart_type,
            "data": {"datasets": [], "labels": []},
            "options": {
                "responsive": True,
                "title": f"{chart_type.capitalize()} Chart",
                "subtitle": "Generated chart",  # Removed f-string
                "xAxis": {"title": "X-Axis", "labels": [], "type": "category"},
                "yAxis": {"title": "Y-Axis", "min": 0},
                "legend": {"display": True},
                "animation": {"duration": self.config.animation_duration},
            },
        }

        # Add data - handle different data formats
        if chart_type == "pie":
            chart_config["data"]["datasets"].append(
                {
                    "data": [item.get("value", item.get("y", 0)) for item in data],
                    "backgroundColor": self.config.default_color_scheme,
                    "label": "Dataset 1",
                }
            )
        else:
            chart_config["data"]["datasets"].append(
                {
                    "data": [item.get("value", item.get("y", 0)) for item in data],
                    "label": "Dataset 1",
                    "borderColor": self.config.default_color_scheme,
                    "fill": chart_type != "line",
                }
            )

        # Add labels - handle different label formats
        chart_config["data"]["labels"] = [
            item.get("label", item.get("x", f"Item {i + 1}"))
            for i, item in enumerate(data)
        ]

        # Override with user options
        chart_config["options"].update(options)

        return chart_config

    def _generate_graph_config(
        self, data: dict, options: dict
    ) -> dict:  # Adjusted type hints
        """
        Generate graph configuration.

        Args:
            data: Graph data (Dict[str, List[Dict[str, Any]]])
            options: Graph options (Dict[str, Any])

        Returns:
            Graph configuration
        """
        # Base configuration
        graph_config = {
            "type": "network",
            "data": {"nodes": [], "links": []},
            "options": {
                "responsive": True,
                "title": "Network Graph",
                "subtitle": "Generated graph",  # Removed f-string
                "nodeSize": 10,
                "linkDistance": 50,
                "charge": -30,
            },
        }

        # Add nodes and links
        graph_config["data"]["nodes"] = [
            {"id": node["id"], "group": node.get("group", 1)} for node in data["nodes"]
        ]
        graph_config["data"]["links"] = [
            {
                "source": link["source"],
                "target": link["target"],
                "value": link.get("value", 1),
            }
            for link in data["links"]
        ]

        # Override with user options
        graph_config["options"].update(options)

        return graph_config

    def _generate_table_config(
        self, data: list, options: dict
    ) -> dict:  # Adjusted type hints
        """
        Generate table configuration.

        Args:
            data: Table data (List[Dict[str, Any]])
            options: Table options (Dict[str, Any])

        Returns:
            Table configuration
        """
        # Base configuration
        table_config = {
            "type": "table",
            "data": {"head": [], "body": []},
            "options": {
                "responsive": True,
                "title": "Data Table",
                "subtitle": "Generated table",  # Removed f-string
                "paging": True,
                "sorting": True,
            },
        }

        # Extract columns from data
        columns = []
        if data:
            columns = list(data[0].keys())
            table_config["data"]["head"] = [[{"text": col} for col in columns]]
            table_config["data"]["body"] = [
                [{"text": str(item[col])} for col in columns] for item in data
            ]

        # Set default options
        default_options = {
            "title": "Data Table",
            "subtitle": "Generated table",  # Removed f-string
            "columns": [{"field": col, "title": col.capitalize()} for col in columns],
            "paging": True,
            "sorting": True,
        }
        table_config["options"].update(
            {
                k: v
                for k, v in default_options.items()
                if k not in table_config["options"]
            }
        )

        # Override with user options
        table_config["options"].update(options)

        return table_config

    def create_chart(
        self, chart_type: str, data: dict, title: str = "Chart"
    ) -> "ChartObject":
        """
        Create a chart object.

        Args:
            chart_type: Type of chart (bar, line, pie, etc.)
            data: Chart data
            title: Chart title

        Returns:
            Chart object
        """
        from pydantic import BaseModel

        class ChartObject(BaseModel):
            chart_type: str
            data: dict
            title: str
            width: int
            height: int

        return ChartObject(
            chart_type=chart_type,
            data=data,
            title=title,
            width=self.config.chart_width,
            height=self.config.chart_height,
        )

    def create_table(
        self, data: list, columns: list[str], title: str = "Table"
    ) -> "TableObject":
        """
        Create a table object.

        Args:
            data: Table data
            columns: Table columns
            title: Table title

        Returns:
            Table object
        """
        from pydantic import BaseModel

        class TableObject(BaseModel):
            data: list
            columns: list[str]
            title: str

        return TableObject(data=data, columns=columns, title=title)

    def export_chart(self, chart: "ChartObject", format: str = "png") -> any:
        """
        Export a chart to various formats.

        Args:
            chart: Chart object to export
            format: Export format (png, svg, json)

        Returns:
            Exported chart data
        """
        if format == "png":
            # Mock PNG data
            return b"fake_png_data"
        elif format == "svg":
            # Mock SVG data
            return f"<svg><title>{chart.title}</title></svg>"
        elif format == "json":
            # Export as JSON
            import json

            return json.dumps(
                {
                    "chart_type": chart.chart_type,
                    "title": chart.title,
                    "data": chart.data,
                    "width": chart.width,
                    "height": chart.height,
                }
            )
        else:
            raise ValueError(f"Unsupported export format: {format}")


# Create a default instance of Visualizations and expose its FastAPI app
# This allows tests to import 'app' from this module.
_default_app_for_visualizations = FastAPI(
    title="Visualizations Service",
    description="Service for generating visualizations.",
    version="0.1.0",
)

visualizations_instance = Visualizations(app=_default_app_for_visualizations)
app = visualizations_instance.app  # Expose the app for testing
