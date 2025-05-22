"""
Visualizations for lib2docScrape.
"""
import logging
import os
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from pydantic import BaseModel, Field
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse

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
        
        logger.info(f"Visualizations initialized with default_chart_type={self.config.default_chart_type}")
        
    def _setup_routes(self) -> None:
        """Set up visualization routes."""
        # Chart API
        @self.app.get("/api/visualizations/chart")
        async def get_chart(
            type: str = None,
            data: str = None,
            options: str = None
        ):
            # Validate chart type
            chart_type = type or self.config.default_chart_type
            if chart_type not in ["bar", "line", "pie", "scatter", "area", "heatmap"]:
                raise HTTPException(status_code=400, detail=f"Invalid chart type: {chart_type}")
                
            # Parse data
            chart_data = []
            if data:
                try:
                    chart_data = json.loads(data)
                except json.JSONDecodeError:
                    raise HTTPException(status_code=400, detail="Invalid data format")
                    
            # Parse options
            chart_options = {}
            if options:
                try:
                    chart_options = json.loads(options)
                except json.JSONDecodeError:
                    raise HTTPException(status_code=400, detail="Invalid options format")
                    
            # Generate chart configuration
            chart_config = self._generate_chart_config(chart_type, chart_data, chart_options)
            
            return chart_config
            
        # Graph API
        @self.app.get("/api/visualizations/graph")
        async def get_graph(
            data: str = None,
            options: str = None
        ):
            if not self.config.enable_graphs:
                raise HTTPException(status_code=403, detail="Graphs are disabled")
                
            # Parse data
            graph_data = {"nodes": [], "links": []}
            if data:
                try:
                    graph_data = json.loads(data)
                except json.JSONDecodeError:
                    raise HTTPException(status_code=400, detail="Invalid data format")
                    
            # Parse options
            graph_options = {}
            if options:
                try:
                    graph_options = json.loads(options)
                except json.JSONDecodeError:
                    raise HTTPException(status_code=400, detail="Invalid options format")
                    
            # Generate graph configuration
            graph_config = self._generate_graph_config(graph_data, graph_options)
            
            return graph_config
            
        # Table API
        @self.app.get("/api/visualizations/table")
        async def get_table(
            data: str = None,
            options: str = None
        ):
            if not self.config.enable_tables:
                raise HTTPException(status_code=403, detail="Tables are disabled")
                
            # Parse data
            table_data = []
            if data:
                try:
                    table_data = json.loads(data)
                except json.JSONDecodeError:
                    raise HTTPException(status_code=400, detail="Invalid data format")
                    
            # Parse options
            table_options = {}
            if options:
                try:
                    table_options = json.loads(options)
                except json.JSONDecodeError:
                    raise HTTPException(status_code=400, detail="Invalid options format")
                    
            # Generate table configuration
            table_config = self._generate_table_config(table_data, table_options)
            
            return table_config
            
    def _generate_chart_config(self, chart_type: str, data: List[Dict[str, Any]], options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate chart configuration.
        
        Args:
            chart_type: Chart type
            data: Chart data
            options: Chart options
            
        Returns:
            Chart configuration
        """
        # Limit data size
        if len(data) > self.config.max_items_per_chart:
            data = data[:self.config.max_items_per_chart]
            
        # Set default options
        default_options = {
            "width": self.config.chart_width,
            "height": self.config.chart_height,
            "colorScheme": self.config.default_color_scheme,
            "animationDuration": self.config.animation_duration,
            "responsive": True,
            "title": f"{chart_type.capitalize()} Chart",
            "subtitle": f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "xAxis": {
                "title": "X Axis",
                "grid": True
            },
            "yAxis": {
                "title": "Y Axis",
                "grid": True
            },
            "legend": {
                "enabled": True,
                "position": "bottom"
            },
            "tooltip": {
                "enabled": True
            }
        }
        
        # Merge with user options
        merged_options = {**default_options, **options}
        
        # Create chart configuration
        chart_config = {
            "type": chart_type,
            "data": data,
            "options": merged_options
        }
        
        return chart_config
        
    def _generate_graph_config(self, data: Dict[str, List[Dict[str, Any]]], options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate graph configuration.
        
        Args:
            data: Graph data
            options: Graph options
            
        Returns:
            Graph configuration
        """
        # Validate data
        if "nodes" not in data or "links" not in data:
            raise HTTPException(status_code=400, detail="Graph data must contain 'nodes' and 'links'")
            
        # Limit data size
        if len(data["nodes"]) > self.config.max_items_per_chart:
            data["nodes"] = data["nodes"][:self.config.max_items_per_chart]
            
            # Filter links to only include nodes that are in the data
            node_ids = {node["id"] for node in data["nodes"]}
            data["links"] = [
                link for link in data["links"]
                if link["source"] in node_ids and link["target"] in node_ids
            ]
            
        # Set default options
        default_options = {
            "width": self.config.chart_width,
            "height": self.config.chart_height,
            "colorScheme": self.config.default_color_scheme,
            "animationDuration": self.config.animation_duration,
            "responsive": True,
            "title": "Network Graph",
            "subtitle": f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "nodeSize": 10,
            "linkWidth": 1,
            "charge": -100,
            "linkDistance": 100,
            "tooltip": {
                "enabled": True
            }
        }
        
        # Merge with user options
        merged_options = {**default_options, **options}
        
        # Create graph configuration
        graph_config = {
            "type": "graph",
            "data": data,
            "options": merged_options
        }
        
        return graph_config
        
    def _generate_table_config(self, data: List[Dict[str, Any]], options: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate table configuration.
        
        Args:
            data: Table data
            options: Table options
            
        Returns:
            Table configuration
        """
        # Limit data size
        if len(data) > self.config.max_items_per_chart:
            data = data[:self.config.max_items_per_chart]
            
        # Extract columns from data
        columns = []
        if data:
            columns = list(data[0].keys())
            
        # Set default options
        default_options = {
            "title": "Data Table",
            "subtitle": f"Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "columns": [{"field": col, "title": col.capitalize()} for col in columns],
            "pagination": True,
            "pageSize": 10,
            "sorting": True,
            "filtering": True,
            "responsive": True,
            "striped": True,
            "bordered": True,
            "hover": True
        }
        
        # Merge with user options
        merged_options = {**default_options, **options}
        
        # Create table configuration
        table_config = {
            "type": "table",
            "data": data,
            "options": merged_options
        }
        
        return table_config
