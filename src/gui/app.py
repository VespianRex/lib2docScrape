from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
import json
import asyncio
from typing import List, Dict, Any
from datetime import datetime
import logging # Import logging

from src.backends.crawl4ai import Crawl4AIBackend, Crawl4AIConfig
from src.backends.base import CrawlResult # Import CrawlResult for type checking

app = FastAPI()
# Corrected path relative to project root
templates = Jinja2Templates(directory="templates")

# Serve static files (assuming static is also at project root)
app.mount("/static", StaticFiles(directory="static"), name="static")

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.crawl_metrics = {
            "pages_crawled": 0,
            "current_depth": 0,
            "successful_requests": 0,
            "failed_requests": 0
        }

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        # Send initial metrics
        await websocket.send_json({
            "type": "metrics",
            "data": self.crawl_metrics
        })

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast_metrics(self):
        """Broadcast current metrics to all connected clients."""
        if not self.active_connections:
            return

        for connection in self.active_connections:
            try:
                await connection.send_json({
                    "type": "metrics",
                    "data": self.crawl_metrics
                })
            except WebSocketDisconnect:
                self.disconnect(connection)

    def update_metrics(self, status: str):
        """Update metrics based on crawl status."""
        self.crawl_metrics["pages_crawled"] += 1
        if status == "success":
            self.crawl_metrics["successful_requests"] += 1
        elif status.startswith("error"):
            self.crawl_metrics["failed_requests"] += 1

    def reset_metrics(self):
        """Reset metrics for new crawl."""
        self.crawl_metrics = {
            "pages_crawled": 0,
            "current_depth": 0,
            "successful_requests": 0,
            "failed_requests": 0
        }

class CrawlRequest(BaseModel):
    url: str

manager = ConnectionManager()

async def progress_callback(url: str, depth: int, status: str):
    """Callback function to handle crawler progress updates."""
    manager.crawl_metrics["current_depth"] = max(manager.crawl_metrics["current_depth"], depth)
    manager.update_metrics(status)
    await manager.broadcast_metrics()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/crawl")
async def crawl(request: CrawlRequest):
    backend = None # Initialize backend to None
    try:
        # Reset metrics for new crawl
        manager.reset_metrics()

        # Initialize backend with progress callback
        config = Crawl4AIConfig(
            max_retries=2,
            timeout=30.0,
            verify_ssl=False,
            max_pages=1000,
            max_depth=10
        )
        backend = Crawl4AIBackend(config=config)
        backend.set_progress_callback(progress_callback)

        # Start crawling
        # Assuming backend.crawl returns a list of CrawlResult objects
        results: List[CrawlResult] = await backend.crawl(request.url)

        # Process the list of CrawlResult objects
        processed_results = []
        for r in results:
             # Ensure 'r' is a CrawlResult object before accessing attributes
             if isinstance(r, CrawlResult) and r.status < 400:
                 processed_results.append({
                     "url": r.url,
                     "content": r.content.get("text", ""), # Assuming text is in content dict
                     "title": r.content.get("title", ""), # Assuming title is in content dict
                     "status": r.status
                 })

        return {
            "status": "success",
            "results": processed_results,
            "total_pages": len(processed_results),
            "metrics": manager.crawl_metrics
        }
    except Exception as e:
        logging.error(f"Error during crawl endpoint: {e}", exc_info=True) # Log the exception
        return {"status": "error", "message": str(e)}
    finally:
        # Ensure backend is closed even if an error occurs
        if backend:
            await backend.close()

def run():
    """Run the FastAPI application using uvicorn."""
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000)