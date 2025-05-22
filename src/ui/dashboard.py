"""
Dashboard for lib2docScrape.
"""
import logging
import os
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

from pydantic import BaseModel, Field
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

logger = logging.getLogger(__name__)

class DashboardConfig(BaseModel):
    """Configuration for the dashboard."""
    title: str = "lib2docScrape Dashboard"
    description: str = "Documentation scraping and processing dashboard"
    theme: str = "light"  # light, dark, auto
    refresh_interval: int = 5  # seconds
    max_items_per_page: int = 20
    enable_websockets: bool = True
    enable_charts: bool = True
    enable_notifications: bool = True
    enable_search: bool = True
    enable_filters: bool = True
    enable_sorting: bool = True
    enable_export: bool = True
    enable_admin: bool = False
    admin_password: Optional[str] = None
    log_level: str = "INFO"
    static_dir: str = "static"
    templates_dir: str = "templates"
    custom_css: Optional[str] = None
    custom_js: Optional[str] = None

class Dashboard:
    """
    Dashboard for lib2docScrape.
    Provides a web interface for monitoring and controlling the system.
    """
    
    def __init__(self, app: FastAPI, config: Optional[DashboardConfig] = None):
        """
        Initialize the dashboard.
        
        Args:
            app: FastAPI application
            config: Optional dashboard configuration
        """
        self.app = app
        self.config = config or DashboardConfig()
        
        # Set up templates
        self.templates = Jinja2Templates(directory=self.config.templates_dir)
        
        # Set up static files
        self.app.mount("/static", StaticFiles(directory=self.config.static_dir), name="static")
        
        # Set up routes
        self._setup_routes()
        
        # Set up WebSocket connection manager
        if self.config.enable_websockets:
            self._setup_websockets()
            
        logger.info(f"Dashboard initialized with title='{self.config.title}'")
        
    def _setup_routes(self) -> None:
        """Set up dashboard routes."""
        # Home page
        @self.app.get("/", response_class=HTMLResponse)
        async def home(request: Request):
            return self.templates.TemplateResponse(
                "dashboard.html",
                {
                    "request": request,
                    "title": self.config.title,
                    "description": self.config.description,
                    "theme": self.config.theme,
                    "enable_charts": self.config.enable_charts,
                    "enable_notifications": self.config.enable_notifications,
                    "enable_search": self.config.enable_search,
                    "enable_filters": self.config.enable_filters,
                    "enable_sorting": self.config.enable_sorting,
                    "enable_export": self.config.enable_export,
                    "enable_admin": self.config.enable_admin,
                    "custom_css": self.config.custom_css,
                    "custom_js": self.config.custom_js
                }
            )
            
        # API routes
        @self.app.get("/api/status")
        async def get_status():
            return {
                "status": "ok",
                "timestamp": datetime.now().isoformat(),
                "version": "1.0.0"
            }
            
        @self.app.get("/api/config")
        async def get_config():
            return self.config.model_dump(exclude={"admin_password"})
            
        # Admin routes
        if self.config.enable_admin:
            @self.app.get("/admin", response_class=HTMLResponse)
            async def admin(request: Request):
                return self.templates.TemplateResponse(
                    "admin.html",
                    {
                        "request": request,
                        "title": f"{self.config.title} - Admin",
                        "description": self.config.description,
                        "theme": self.config.theme
                    }
                )
                
    def _setup_websockets(self) -> None:
        """Set up WebSocket connections."""
        # Connection manager
        class ConnectionManager:
            def __init__(self):
                self.active_connections: List[WebSocket] = []
                
            async def connect(self, websocket: WebSocket):
                await websocket.accept()
                self.active_connections.append(websocket)
                
            def disconnect(self, websocket: WebSocket):
                self.active_connections.remove(websocket)
                
            async def broadcast(self, message: Dict[str, Any]):
                for connection in self.active_connections:
                    try:
                        await connection.send_json(message)
                    except WebSocketDisconnect:
                        self.disconnect(connection)
                        
        self.connection_manager = ConnectionManager()
        
        # WebSocket endpoint
        @self.app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await self.connection_manager.connect(websocket)
            try:
                while True:
                    data = await websocket.receive_json()
                    # Process received data
                    await websocket.send_json({"status": "received", "data": data})
            except WebSocketDisconnect:
                self.connection_manager.disconnect(websocket)
                
    async def broadcast_update(self, data: Dict[str, Any]) -> None:
        """
        Broadcast an update to all connected clients.
        
        Args:
            data: Update data
        """
        if self.config.enable_websockets:
            await self.connection_manager.broadcast({
                "type": "update",
                "timestamp": datetime.now().isoformat(),
                "data": data
            })
            
    async def broadcast_notification(self, message: str, level: str = "info") -> None:
        """
        Broadcast a notification to all connected clients.
        
        Args:
            message: Notification message
            level: Notification level (info, warning, error, success)
        """
        if self.config.enable_websockets and self.config.enable_notifications:
            await self.connection_manager.broadcast({
                "type": "notification",
                "timestamp": datetime.now().isoformat(),
                "level": level,
                "message": message
            })
