#!/usr/bin/env python3
import argparse
import asyncio
import json
import logging
import os
import re
from datetime import datetime
from typing import Any, Optional

import yaml
from fastapi import (
    BackgroundTasks,
    FastAPI,
    HTTPException,
    Request,
    WebSocket,
    WebSocketDisconnect,
)
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from .backends.crawl4ai_backend import Crawl4AIBackend, Crawl4AIConfig
from .backends.file_backend import FileBackend
from .backends.lightpanda_backend import LightpandaBackend, LightpandaConfig
from .backends.selector import BackendCriteria, BackendSelector
from .benchmarking.backend_benchmark import BackendBenchmark
from .crawler import CrawlerConfig, CrawlTarget, DocumentationCrawler
from .organizers.doc_organizer import DocumentOrganizer, OrganizationConfig
from .processors.content.models import ProcessorConfig as ProcessingConfig
from .processors.content_processor import ContentProcessor
from .processors.quality_checker import QualityChecker, QualityConfig
from .utils.helpers import setup_logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory storage for web interface
scraping_results_storage: dict[str, dict] = {}
active_scraper = None
is_scraping = False
library_operations: dict[str, dict] = {}


async def validate_package_name(package_name: str) -> bool:
    """
    Validate a package name format.

    Args:
        package_name: The package name to validate

    Returns:
        bool: True if valid, False otherwise
    """
    try:
        if not re.match(r"^[a-zA-Z0-9][-a-zA-Z0-9_.]*$", package_name):
            return False
        return True
    except Exception:
        return False


async def run_uv_command(command_args: list[str]) -> tuple[int, str, str]:
    """
    Run a UV package manager command.

    Args:
        command_args: List of command arguments to pass to uv

    Returns:
        tuple: (return_code, stdout, stderr)
    """
    try:
        process = await asyncio.create_subprocess_exec(
            "uv",
            *command_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout_bytes, stderr_bytes = await process.communicate()

        stdout = stdout_bytes.decode("utf-8") if stdout_bytes else ""
        stderr = stderr_bytes.decode("utf-8") if stderr_bytes else ""

        return process.returncode, stdout, stderr

    except Exception as e:
        return 1, "", str(e)


class AppConfig(BaseModel):
    """Application configuration model."""

    crawler: CrawlerConfig
    processing: ProcessingConfig
    quality: QualityConfig
    organization: OrganizationConfig
    crawl4ai: Crawl4AIConfig
    lightpanda: Optional[dict[str, Any]] = None
    library_tracking: Optional[dict[str, Any]] = None
    benchmarking: Optional[dict[str, Any]] = None
    logging: dict[str, Any]


class LibraryOperation(BaseModel):
    """Model for library operations."""

    operation: str
    package_name: str
    status: str = "pending"
    progress: int = 0
    error: Optional[str] = None

    @classmethod
    def validate_package_name(cls, v: str) -> str:
        if not re.match(r"^[a-zA-Z0-9][-a-zA-Z0-9_.]*$", v):
            raise ValueError("Invalid package name format")
        return v


class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.scraping_connections: list[WebSocket] = []
        self.library_connections: list[WebSocket] = []
        self.scraping_metrics = {
            "pages_scraped": 0,
            "current_depth": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "pages_per_second": 0.0,
            "memory_usage": "0 MB",
            "cpu_usage": "0%",
        }
        self.scraping_status = {"is_running": False, "current_url": None, "progress": 0}

    async def connect(self, websocket: WebSocket, connection_type: str = "scraping"):
        logging.info(f"New WebSocket connection attempt - Type: {connection_type}")
        await websocket.accept()
        if connection_type == "scraping":
            self.scraping_connections.append(websocket)
            logging.info("Scraping connection established - Sending initial status")
            await websocket.send_json(
                {"type": "connection_established", "data": self.scraping_status}
            )
        elif connection_type == "library":
            self.library_connections.append(websocket)
            logging.info("Library connection established")
            await websocket.send_json(
                {"type": "connection_established", "data": {"status": "connected"}}
            )

    def disconnect(self, websocket: WebSocket):
        if websocket in self.scraping_connections:
            self.scraping_connections.remove(websocket)
        if websocket in self.library_connections:
            self.library_connections.remove(websocket)

    async def broadcast_metrics(self):
        if not self.scraping_connections:
            return

        for connection in self.scraping_connections:
            try:
                await connection.send_json(
                    {"type": "metrics", "data": self.scraping_metrics}
                )
            except WebSocketDisconnect:
                self.disconnect(connection)

    async def broadcast_scraping_update(self, update: dict):
        if not self.scraping_connections:
            logging.info("No scraping connections available for broadcast")
            return

        logging.info(
            f"Broadcasting scraping update to {len(self.scraping_connections)} connections: {update}"
        )
        for connection in self.scraping_connections:
            try:
                await connection.send_json(
                    {"type": "scraping_progress", "data": update}
                )
            except WebSocketDisconnect:
                logging.warning("WebSocket disconnected during broadcast")
                self.disconnect(connection)

    def update_metrics(self, status: str):
        self.scraping_metrics["pages_scraped"] += 1
        if status == "success":
            self.scraping_metrics["successful_requests"] += 1
        elif status.startswith("error"):
            self.scraping_metrics["failed_requests"] += 1

    def reset_metrics(self):
        self.scraping_metrics = {
            "pages_scraped": 0,
            "current_depth": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "pages_per_second": 0.0,
            "memory_usage": "0 MB",
            "cpu_usage": "0%",
        }


# FastAPI Application Setup
app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize connection manager
manager = ConnectionManager()


# Basic routes for testing and default functionality
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the home page."""
    return templates.TemplateResponse(request, "scraping_dashboard.html", {"request": request})


@app.get("/api/scraping/backends")
async def get_available_backends():
    """Get available scraping backends."""
    backends = ["crawl4ai", "file"]

    # Check if Lightpanda is available
    try:
        import subprocess

        result = subprocess.run(
            ["lightpanda", "--version"],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            backends.append("lightpanda")
    except (FileNotFoundError, subprocess.SubprocessError):
        pass

    return backends


@app.get("/api/scraping/status")
async def get_scraping_status():
    """Get current scraping status."""
    return manager.scraping_status


@app.get("/api/scraping/results")
async def list_scraping_results():
    """Get all scraping results."""
    return [
        {
            "id": result_id,
            "url": data.get("url", ""),
            "title": data.get("title", ""),
            "status": data.get("status", "unknown"),
            "timestamp": data["timestamp"].isoformat()
            if isinstance(data.get("timestamp"), datetime)
            else data.get("timestamp"),
        }
        for result_id, data in scraping_results_storage.items()
    ]


@app.get("/api/scraping/download/json")
async def download_results_json():
    """Download all scraping results as JSON."""
    if not scraping_results_storage:
        raise HTTPException(status_code=500, detail="No scraping results available")

    return JSONResponse(
        content=scraping_results_storage,
        headers={"Content-Disposition": "attachment; filename=scraping_results.json"},
    )


@app.get("/libraries", response_class=HTMLResponse)
async def libraries(request: Request):
    """Render the libraries page."""
    return templates.TemplateResponse(request, "libraries.html", {"request": request})


@app.websocket("/ws/scraping")
async def scraping_websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for scraping updates."""
    await manager.connect(websocket, "scraping")
    try:
        while True:
            data = await websocket.receive_json()
            if data["type"] == "scraping_progress":
                # Echo the progress update back to the client
                await websocket.send_json(
                    {"type": "scraping_progress", "data": data["data"]}
                )
                # Also broadcast to other connected clients
                await manager.broadcast_scraping_update(data["data"])
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.post("/api/scraping/results")
async def store_scraping_results(results: dict):
    """Store scraping results."""
    scraping_id = results.get("scraping_id")
    if not scraping_id:
        scraping_id = f"scrape_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        results["scraping_id"] = scraping_id

    # Ensure timestamp is in ISO format if it's a datetime object
    timestamp = results.get("timestamp", datetime.now())
    if isinstance(timestamp, datetime):
        results["timestamp"] = timestamp.isoformat()
    else:
        # If it's already a string, assume it's correctly formatted or handle accordingly
        results["timestamp"] = str(timestamp)  # Fallback, ideally validate format

    scraping_results_storage[scraping_id] = results

    return {"status": "success", "scraping_id": scraping_id}


@app.get("/api/scraping/results/{scraping_id}")
async def get_scraping_results(scraping_id: str):
    """Get scraping results by ID."""
    if scraping_id not in scraping_results_storage:
        raise HTTPException(status_code=404, detail="Scraping results not found")

    # Ensure datetime is serialized
    result = scraping_results_storage[scraping_id]
    if isinstance(result.get("timestamp"), datetime):
        result["timestamp"] = result["timestamp"].isoformat()

    # Also serialize datetime in nested structures if necessary, for example, in 'results' list
    if "results" in result and isinstance(result["results"], list):
        for item in result["results"]:
            if isinstance(
                item.get("timestamp"), datetime
            ):  # Assuming items might have timestamps
                item["timestamp"] = item["timestamp"].isoformat()
            if isinstance(item.get("content"), dict) and isinstance(
                item["content"].get("last_modified"), datetime
            ):
                item["content"]["last_modified"] = item["content"][
                    "last_modified"
                ].isoformat()

    return result


@app.post("/api/libraries/{package_name}")
async def install_library_docs(package_name: str, background_tasks: BackgroundTasks):
    """Fetch and install library documentation."""
    if not await validate_package_name(package_name):
        raise HTTPException(status_code=400, detail="Invalid package name")

    # Generate operation ID
    operation_id = f"install_{package_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # Store initial operation state
    library_operations[operation_id] = {
        "operation_id": operation_id,
        "package_name": package_name,
        "operation": "install",
        "status": "pending",
        "start_time": datetime.now().isoformat(),  # Ensure stored as ISO string
        "end_time": None,
        "output": "",
        "error": "",
    }

    # Define background task for fetching library documentation
    async def fetch_library_docs_task():
        try:
            # Update operation status
            library_operations[operation_id]["status"] = "running"

            # TODO: Replace with actual library documentation fetching logic
            # For now, simulate the process with a delay
            await asyncio.sleep(2)

            # Update operation with results
            library_operations[operation_id].update(
                {
                    "status": "completed",
                    "end_time": datetime.now().isoformat(),  # Ensure stored as ISO string
                    "output": f"Documentation for {package_name} has been successfully fetched and processed.",
                    "error": "",
                }
            )

        except Exception as e:
            # Handle any exceptions
            library_operations[operation_id].update(
                {
                    "status": "failed",
                    "end_time": datetime.now().isoformat(),  # Ensure stored as ISO string
                    "error": str(e),
                }
            )

    # Start background task
    background_tasks.add_task(fetch_library_docs_task)

    return {"operation_id": operation_id, "status": "pending"}


@app.delete("/api/libraries/{package_name}")
async def remove_library_docs(package_name: str, background_tasks: BackgroundTasks):
    """Remove library documentation."""
    if not await validate_package_name(package_name):
        raise HTTPException(status_code=400, detail="Invalid package name")

    # Generate operation ID
    operation_id = f"remove_{package_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # Store initial operation state
    library_operations[operation_id] = {
        "operation_id": operation_id,
        "package_name": package_name,
        "operation": "uninstall",
        "status": "pending",
        "start_time": datetime.now().isoformat(),  # Ensure stored as ISO string
        "end_time": None,
        "output": "",
        "error": "",
    }

    # Define background task for removing library documentation
    async def remove_library_docs_task():
        try:
            # Update operation status
            library_operations[operation_id]["status"] = "running"

            # TODO: Replace with actual logic to remove library documentation
            # For now, simulate the process with a delay
            await asyncio.sleep(1.5)

            # Update operation with results
            library_operations[operation_id].update(
                {
                    "status": "completed",
                    "end_time": datetime.now().isoformat(),  # Ensure stored as ISO string
                    "output": f"Documentation for {package_name} has been successfully removed.",
                    "error": "",
                }
            )

        except Exception as e:
            # Handle any exceptions
            library_operations[operation_id].update(
                {
                    "status": "failed",
                    "end_time": datetime.now().isoformat(),  # Ensure stored as ISO string
                    "error": str(e),
                }
            )

    # Start background task
    background_tasks.add_task(remove_library_docs_task)

    return {"operation_id": operation_id, "status": "pending"}


@app.get("/api/libraries/operation/{operation_id}")
async def get_library_operation_status(operation_id: str):
    """Get status of a library operation."""
    if operation_id not in library_operations:
        raise HTTPException(status_code=404, detail="Operation not found")

    return library_operations[operation_id]


@app.post("/crawl")
async def start_crawl(request: dict):
    """Start a crawl for a given URL."""
    global is_scraping

    try:
        url = request.get("url")
        if not url:
            raise HTTPException(status_code=400, detail="URL is required")

        backend_type = request.get("backend", "crawl4ai")
        max_depth = request.get("max_depth", 10)

        is_scraping = True
        manager.scraping_status.update(
            {"is_running": True, "current_url": url, "progress": 0}
        )

        # Create a backend based on selection
        backend = None
        if backend_type == "crawl4ai":
            backend = Crawl4AIBackend()
        elif backend_type == "file":
            from .backends.file import FileBackend

            backend = FileBackend()
        elif backend_type == "lightpanda":
            try:
                backend = LightpandaBackend()
            except Exception as e:
                raise HTTPException(
                    status_code=500,
                    detail=f"Failed to initialize Lightpanda backend: {str(e)}",
                ) from e
        else:
            raise HTTPException(status_code=400, detail="Invalid backend type")

        # Start crawling
        results = await backend.crawl(url, max_depth=max_depth)

        # Store results
        scraping_id = f"scrape_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        scraping_results_storage[scraping_id] = {
            "scraping_id": scraping_id,
            "timestamp": datetime.now().isoformat(),
            "url": url,
            "status": "completed",
            "results": [result.model_dump() for result in results],
        }

        # Update status
        is_scraping = False
        manager.scraping_status.update(
            {"is_running": False, "current_url": "", "progress": 100}
        )

        return {
            "status": "success",
            "scraping_id": scraping_id,
            "results": [result.model_dump() for result in results],
        }
    except Exception as e:
        is_scraping = False
        manager.scraping_status.update(
            {"is_running": False, "current_url": "", "progress": 0}
        )
        logging.error(f"Error during crawl: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}


# CLI Functions
def load_config(config_path: str) -> AppConfig:
    """Load configuration from file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path) as f:
        if config_path.endswith(".json"):
            config_data = json.load(f)
        elif config_path.endswith(".yaml") or config_path.endswith(".yml"):
            config_data = yaml.safe_load(f)
        else:
            raise ValueError("Configuration file must be JSON or YAML")

    return AppConfig(**config_data)


def setup_crawler(config: AppConfig) -> DocumentationCrawler:
    """Setup crawler with configuration."""
    # Initialize components
    backend_selector = BackendSelector()
    content_processor = ContentProcessor(config=config.processing)
    quality_checker = QualityChecker(config=config.quality)
    document_organizer = DocumentOrganizer(config=config.organization)

    # Setup Crawl4AI backend
    crawl4ai_backend = Crawl4AIBackend(config=config.crawl4ai)
    backend_selector.register_backend(
        crawl4ai_backend,
        BackendCriteria(
            priority=100,
            content_types=["text/html", "text/plain"],
            url_patterns=["*"],
            max_load=0.8,
            min_success_rate=0.7,
        ),
    )

    # Setup Lightpanda backend if configured
    if config.lightpanda:
        try:
            lightpanda_config = LightpandaConfig(**config.lightpanda)
            lightpanda_backend = LightpandaBackend(config=lightpanda_config)
            backend_selector.register_backend(
                lightpanda_backend,
                BackendCriteria(
                    priority=90,  # Slightly lower priority than Crawl4AI
                    content_types=["text/html"],
                    url_patterns=["*"],
                    max_load=0.8,
                    min_success_rate=0.7,
                ),
            )
            logging.info("Lightpanda backend registered")
        except Exception as e:
            logging.warning(f"Failed to register Lightpanda backend: {e}")

    # Create and return crawler
    return DocumentationCrawler(
        config=config.crawler,
        backend_selector=backend_selector,
        content_processor=content_processor,
        quality_checker=quality_checker,
        document_organizer=document_organizer,
    )


def create_app(config_path: Optional[str] = None) -> FastAPI:
    global \
        app_config, \
        active_scraper, \
        document_organizer, \
        library_tracker, \
        content_processor, \
        quality_checker, \
        backend_selector, \
        crawler

    if config_path:
        app_config = load_config(config_path)
    else:
        # Load default config
        app_config = load_config("config.yaml")

    # Set up logging
    log_level = "DEBUG" if app_config.logging.get("debug", False) else "INFO"
    setup_logging(level=log_level)

    # --- Crawler Setup ---
    crawler = setup_crawler(app_config)

    # --- Routes ---
    @app.get("/", response_class=HTMLResponse)
    async def home(request: Request):
        """Render the home page."""
        return templates.TemplateResponse(
            request, "scraping_dashboard.html", {"request": request}
        )

    @app.get("/api/scraping/backends")
    async def get_available_backends():
        """Get available scraping backends."""
        backends = ["crawl4ai", "file"]

        # Check if Lightpanda is available
        try:
            import subprocess

            result = subprocess.run(
                ["lightpanda", "--version"],
                capture_output=True,
                text=True,
                check=False,
            )
            if result.returncode == 0:
                backends.append("lightpanda")
        except (FileNotFoundError, subprocess.SubprocessError):
            pass

        return backends

    @app.get("/api/scraping/status")
    async def get_scraping_status():
        """Get current scraping status."""
        return manager.scraping_status

    @app.get("/api/scraping/results")
    async def list_scraping_results():
        """Get all scraping results."""
        return [
            {
                "scraping_id": scraping_id,
                "timestamp": data["timestamp"].isoformat()
                if isinstance(data.get("timestamp"), datetime)
                else data.get("timestamp"),
                "url": data.get("url"),  # Use .get() for safety
                "status": data.get("status"),  # Use .get() for safety
                "pages_processed": len(data.get("results", [])),
            }
            for scraping_id, data in scraping_results_storage.items()
        ]

    @app.get("/api/scraping/results/{scraping_id}")
    async def get_scraping_results(scraping_id: str):
        """Get scraping results by ID."""
        if scraping_id not in scraping_results_storage:
            raise HTTPException(status_code=404, detail="Scraping results not found")

        # Ensure datetime is serialized
        result = scraping_results_storage[scraping_id]
        if isinstance(result.get("timestamp"), datetime):
            result["timestamp"] = result["timestamp"].isoformat()

        # Also serialize datetime in nested structures if necessary, for example, in 'results' list
        if "results" in result and isinstance(result["results"], list):
            for item in result["results"]:
                if isinstance(
                    item.get("timestamp"), datetime
                ):  # Assuming items might have timestamps
                    item["timestamp"] = item["timestamp"].isoformat()
                if isinstance(item.get("content"), dict) and isinstance(
                    item["content"].get("last_modified"), datetime
                ):
                    item["content"]["last_modified"] = item["content"][
                        "last_modified"
                    ].isoformat()

        return result

    @app.get("/api/scraping/download/{format}")
    async def download_results(format: str):
        """Download scraping results in specified format."""
        if format not in ["json", "markdown", "html"]:
            raise HTTPException(status_code=400, detail="Invalid format specified")

        try:
            if not scraping_results_storage:
                raise HTTPException(
                    status_code=404, detail="No scraping results available"
                )

            latest_id = max(scraping_results_storage.keys())
            results = scraping_results_storage[latest_id]

            if format == "json":
                return JSONResponse(content=results)
            elif format == "markdown":
                markdown_content = "# Documentation Export\n\n"
                for doc in results["results"]:
                    markdown_content += (
                        f"## {doc.get('content', {}).get('title', 'Untitled')}\n\n"
                    )
                    markdown_content += f"{doc.get('content', {}).get('text', '')}\n\n"
                return PlainTextResponse(content=markdown_content)
            else:  # html
                html_content = "<html><body>"
                for doc in results["results"]:
                    html_content += (
                        f"<h2>{doc.get('content', {}).get('title', 'Untitled')}</h2>"
                    )
                    html_content += (
                        f"<div>{doc.get('content', {}).get('text', '')}</div>"
                    )
                html_content += "</body></html>"
                return HTMLResponse(content=html_content)

        except Exception as e:
            logging.error(f"Error downloading results: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e)) from e

    @app.get("/libraries", response_class=HTMLResponse)
    async def libraries(request: Request):
        """Render the library management page."""
        return templates.TemplateResponse("libraries.html", {"request": request})

    @app.websocket("/ws/library-updates")
    async def library_websocket_endpoint(websocket: WebSocket):
        """WebSocket endpoint for library operation updates."""
        await manager.connect(websocket, "library")
        try:
            while True:
                await websocket.receive_text()  # Keep connection alive
        except WebSocketDisconnect:
            manager.disconnect(websocket)

    @app.post("/crawl")
    async def start_crawl(request: dict):
        """Start a crawl for a given URL."""
        global is_scraping

        try:
            url = request.get("url")
            if not url:
                raise HTTPException(status_code=400, detail="URL is required")

            backend_type = request.get("backend", "crawl4ai")
            max_depth = request.get("max_depth", 10)

            is_scraping = True
            manager.scraping_status.update(
                {"is_running": True, "current_url": url, "progress": 0}
            )

            # Create a backend based on selection
            backend = None
            if backend_type == "crawl4ai":
                backend = Crawl4AIBackend()
            elif backend_type == "file":
                backend = FileBackend()
            elif backend_type == "lightpanda":
                try:
                    backend = LightpandaBackend()
                except Exception as e:
                    raise HTTPException(
                        status_code=500,
                        detail=f"Failed to initialize Lightpanda backend: {str(e)}",
                    ) from e
            else:
                raise HTTPException(status_code=400, detail="Invalid backend type")

            # Start crawling
            results = await backend.crawl(url, max_depth=max_depth)

            # Store results
            scraping_id = f"scrape_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            scraping_results_storage[scraping_id] = {
                "scraping_id": scraping_id,
                "timestamp": datetime.now().isoformat(),  # Ensure stored as ISO string
                "url": url,
                "status": "completed",
                "results": [result.model_dump() for result in results],
            }

            # Update status
            is_scraping = False
            manager.scraping_status.update(
                {"is_running": False, "current_url": "", "progress": 100}
            )

            return {
                "status": "success",
                "scraping_id": scraping_id,
                "results": [result.model_dump() for result in results],
            }
        except Exception as e:
            is_scraping = False
            manager.scraping_status.update(
                {"is_running": False, "current_url": "", "progress": 0}
            )
            logging.error(f"Error during crawl: {str(e)}", exc_info=True)
            return {"status": "error", "message": str(e)}

    @app.post("/api/scraping/results")
    async def store_scraping_results(results: dict):
        """Store scraping results."""
        scraping_id = results.get("scraping_id")
        if not scraping_id:
            scraping_id = f"scrape_{datetime.now().strftime('%Y%m%d%H%M%S')}"
            results["scraping_id"] = scraping_id

        # Ensure timestamp is in ISO format if it's a datetime object
        timestamp = results.get("timestamp", datetime.now())
        if isinstance(timestamp, datetime):
            results["timestamp"] = timestamp.isoformat()
        else:
            # If it's already a string, assume it's correctly formatted or handle accordingly
            results["timestamp"] = str(timestamp)  # Fallback, ideally validate format

        scraping_results_storage[scraping_id] = results

        return {"status": "success", "scraping_id": scraping_id}

    @app.post("/api/libraries/{package_name}")
    async def install_library_docs(
        package_name: str, background_tasks: BackgroundTasks
    ):
        """Fetch and install library documentation."""
        if not await validate_package_name(package_name):
            raise HTTPException(status_code=400, detail="Invalid package name")

        # Generate operation ID
        operation_id = (
            f"install_{package_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )

        # Store initial operation state
        library_operations[operation_id] = {
            "operation_id": operation_id,
            "package_name": package_name,
            "operation": "install",
            "status": "pending",
            "start_time": datetime.now().isoformat(),  # Ensure stored as ISO string
            "end_time": None,
            "output": "",
            "error": "",
        }

        # Define background task for fetching library documentation
        async def fetch_library_docs_task():
            try:
                # Update operation status
                library_operations[operation_id]["status"] = "running"

                # TODO: Replace with actual library documentation fetching logic
                # For now, simulate the process with a delay
                await asyncio.sleep(2)

                # Update operation with results
                library_operations[operation_id].update(
                    {
                        "status": "completed",
                        "end_time": datetime.now().isoformat(),  # Ensure stored as ISO string
                        "output": f"Documentation for {package_name} has been successfully fetched and processed.",
                        "error": "",
                    }
                )

            except Exception as e:
                # Handle any exceptions
                library_operations[operation_id].update(
                    {
                        "status": "failed",
                        "end_time": datetime.now().isoformat(),  # Ensure stored as ISO string
                        "error": str(e),
                    }
                )

        # Start background task
        background_tasks.add_task(fetch_library_docs_task)

        return {"operation_id": operation_id, "status": "pending"}

    @app.delete("/api/libraries/{package_name}")
    async def remove_library_docs(package_name: str, background_tasks: BackgroundTasks):
        """Remove library documentation."""
        if not await validate_package_name(package_name):
            raise HTTPException(status_code=400, detail="Invalid package name")

        # Generate operation ID
        operation_id = (
            f"remove_{package_name}_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        )

        # Store initial operation state
        library_operations[operation_id] = {
            "operation_id": operation_id,
            "package_name": package_name,
            "operation": "uninstall",
            "status": "pending",
            "start_time": datetime.now().isoformat(),  # Ensure stored as ISO string
            "end_time": None,
            "output": "",
            "error": "",
        }

        # Define background task for removing library documentation
        async def remove_library_docs_task():
            try:
                # Update operation status
                library_operations[operation_id]["status"] = "running"

                # TODO: Replace with actual logic to remove library documentation
                # For now, simulate the process with a delay
                await asyncio.sleep(1.5)

                # Update operation with results
                library_operations[operation_id].update(
                    {
                        "status": "completed",
                        "end_time": datetime.now().isoformat(),  # Ensure stored as ISO string
                        "output": f"Documentation for {package_name} has been successfully removed.",
                        "error": "",
                    }
                )

            except Exception as e:
                # Handle any exceptions
                library_operations[operation_id].update(
                    {
                        "status": "failed",
                        "end_time": datetime.now().isoformat(),  # Ensure stored as ISO string
                        "error": str(e),
                    }
                )

        # Start background task
        background_tasks.add_task(remove_library_docs_task)

        return {"operation_id": operation_id, "status": "pending"}

    @app.get("/api/libraries/operation/{operation_id}")
    async def get_library_operation_status(operation_id: str):
        """Get status of a library operation."""
        if operation_id not in library_operations:
            raise HTTPException(status_code=404, detail="Operation not found")

        return library_operations[operation_id]

    return app


async def run_crawler(
    crawler: DocumentationCrawler, targets: list[CrawlTarget]
) -> None:
    """Run crawler for specified targets."""
    try:
        for target in targets:
            logging.info(f"Starting crawl for target: {target.url}")
            result = await crawler.crawl(target)

            logging.info(f"Crawl completed for {target.url}")
            logging.info(f"Pages crawled: {result.stats.pages_crawled}")
            logging.info(f"Successful crawls: {result.stats.successful_crawls}")
            logging.info(f"Failed crawls: {result.stats.failed_crawls}")
            logging.info(f"Quality issues: {result.stats.quality_issues}")
            logging.info(
                f"Average time per page: {result.stats.average_time_per_page:.2f}s"
            )

            # Output results
            output_file = f"crawl_result_{result.stats.start_time:%Y%m%d_%H%M%S}.json"
            with open(output_file, "w") as f:
                json.dump(
                    {
                        "target": target.model_dump(),
                        "stats": result.stats.model_dump(),
                        "documents": result.documents,
                        "issues": [issue.model_dump() for issue in result.issues],
                        "metrics": {
                            k: v.model_dump() for k, v in result.metrics.items()
                        },
                    },
                    f,
                    indent=2,
                    default=str,
                )
            logging.info(f"Results saved to {output_file}")

    finally:
        await crawler.close()


def parse_args() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Documentation Crawler CLI",
        epilog="""
Environment Variables:
  LIB2DOCSCRAPE_CONFIG    Default configuration file path
  LIB2DOCSCRAPE_LOG_LEVEL Override logging level (DEBUG, INFO, WARNING, ERROR)
  LIB2DOCSCRAPE_OUTPUT_DIR Directory for scraped documentation
  LIB2DOCSCRAPE_CACHE_DIR  Directory for caching scraped content

Examples:
  # Basic usage with default config
  lib2docscrape scrape -t targets.yaml

  # Custom config with verbose logging
  lib2docscrape scrape -c custom_config.yaml -t targets.yaml -v

  # Start web interface
  lib2docscrape serve

  # Benchmark backends
  lib2docscrape benchmark -u https://docs.python.org/3/ -b all

  # Track library versions
  lib2docscrape library track -n python -v 3.9,3.10,3.11

Configuration File Example (config.yaml):
  crawler:
    concurrent_requests: 5
    requests_per_second: 10
    max_retries: 3
  processing:
    allowed_tags: [p, h1, h2, code]
    max_content_length: 5000000
  quality:
    min_content_length: 100
    required_metadata_fields: [title, description]

Target File Example (targets.yaml):
  - url: "https://docs.example.com/"
    depth: 2
    follow_external: false
    content_types: ["text/html"]
    exclude_patterns: ["/downloads/"]
""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Scrape command
    scrape_parser = subparsers.add_parser("scrape", help="Scrape documentation")
    scrape_parser.add_argument(
        "-c",
        "--config",
        type=str,
        default="config.yaml",
        help="""Path to configuration file (JSON or YAML).
Controls crawler behavior, processing rules, and quality checks.
Default: config.yaml
Environment Variable: LIB2DOCSCRAPE_CONFIG""",
    )

    scrape_parser.add_argument(
        "-t",
        "--targets",
        type=str,
        required=True,
        help="""Path to targets file (JSON or YAML).
Defines the documentation sites to crawl and their parameters.
Required. Must contain at least one target configuration.""",
    )

    scrape_parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="""Enable verbose logging.
Shows detailed progress and debug information.
Can also be enabled via LIB2DOCSCRAPE_LOG_LEVEL=DEBUG""",
    )

    scrape_parser.add_argument(
        "-d",
        "--distributed",
        action="store_true",
        help="""Use distributed crawling.
Enables parallel processing of crawl targets using multiple workers.""",
    )

    scrape_parser.add_argument(
        "-w",
        "--workers",
        type=int,
        default=5,
        help="""Number of workers for distributed crawling (default: 5).
Only used when --distributed is specified.""",
    )

    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Start web server")
    serve_parser.add_argument(
        "-p",
        "--port",
        type=int,
        default=8000,
        help="Port to run the server on (default: 8000)",
    )

    serve_parser.add_argument(
        "-h",
        "--host",
        type=str,
        default="127.0.0.1",
        help="Host to bind the server to (default: 127.0.0.1)",
    )

    # Benchmark command
    benchmark_parser = subparsers.add_parser("benchmark", help="Benchmark backends")
    benchmark_parser.add_argument(
        "-u",
        "--urls",
        type=str,
        required=True,
        help="Comma-separated list of URLs to benchmark",
    )

    benchmark_parser.add_argument(
        "-b",
        "--backends",
        type=str,
        default="all",
        help="Comma-separated list of backends to benchmark (default: all)",
    )

    benchmark_parser.add_argument(
        "-o", "--output", type=str, help="Output file for benchmark results"
    )

    benchmark_parser.add_argument(
        "-c",
        "--config",
        type=str,
        default="config.yaml",
        help="Path to configuration file (JSON or YAML)",
    )

    # Library command
    library_parser = subparsers.add_parser("library", help="Library version management")
    library_subparsers = library_parser.add_subparsers(
        dest="library_command", help="Library command"
    )

    # Track command
    track_parser = library_subparsers.add_parser("track", help="Track library versions")
    track_parser.add_argument(
        "-n", "--name", type=str, required=True, help="Library name"
    )

    track_parser.add_argument(
        "-v",
        "--versions",
        type=str,
        required=True,
        help="Comma-separated list of versions to track",
    )

    track_parser.add_argument(
        "-u", "--url", type=str, help="Base URL for library documentation (optional)"
    )

    # Compare command
    compare_parser = library_subparsers.add_parser(
        "compare", help="Compare library versions"
    )
    compare_parser.add_argument(
        "-n", "--name", type=str, required=True, help="Library name"
    )

    compare_parser.add_argument(
        "-v1", "--version1", type=str, required=True, help="First version"
    )

    compare_parser.add_argument(
        "-v2", "--version2", type=str, required=True, help="Second version"
    )

    compare_parser.add_argument(
        "-o", "--output", type=str, help="Output file for comparison results"
    )

    # List command
    list_parser = library_subparsers.add_parser("list", help="List tracked libraries")
    list_parser.add_argument("-n", "--name", type=str, help="Library name (optional)")

    # Visualize command
    visualize_parser = library_subparsers.add_parser(
        "visualize", help="Visualize library version history"
    )
    visualize_parser.add_argument(
        "-n", "--name", type=str, required=True, help="Library name"
    )
    visualize_parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output file for visualization (default: <library_name>_version_history.html)",
    )

    # Categorize command
    categorize_parser = library_subparsers.add_parser(
        "categorize", help="Categorize library documentation"
    )
    categorize_parser.add_argument(
        "-n", "--name", type=str, required=True, help="Library name"
    )
    categorize_parser.add_argument(
        "-v", "--version", type=str, help="Library version (optional)"
    )
    categorize_parser.add_argument(
        "-c",
        "--categories",
        type=int,
        default=10,
        help="Number of categories to create (default: 10)",
    )
    categorize_parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output file for categorization model (default: <library_name>_categories.pkl)",
    )

    # Topics command
    topics_parser = library_subparsers.add_parser(
        "topics", help="Extract topics from library documentation"
    )
    topics_parser.add_argument(
        "-n", "--name", type=str, required=True, help="Library name"
    )
    topics_parser.add_argument(
        "-v", "--version", type=str, help="Library version (optional)"
    )
    topics_parser.add_argument(
        "-t",
        "--topics",
        type=int,
        default=10,
        help="Number of topics to extract (default: 10)",
    )
    topics_parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output file for topic model (default: <library_name>_topics.pkl)",
    )

    # Package command
    package_parser = library_subparsers.add_parser(
        "package", help="Manage Python packages"
    )
    package_parser.add_argument(
        "package_action",
        choices=["install", "uninstall", "list"],
        help="Package action to perform",
    )
    package_parser.add_argument(
        "package_name", type=str, nargs="?", help="Package name"
    )
    package_parser.add_argument(
        "-v", "--version", type=str, help="Package version (for install)"
    )
    package_parser.add_argument(
        "--use-uv",
        action="store_true",
        default=True,
        help="Use uv package manager (default: True)",
    )
    package_parser.add_argument(
        "--use-pip", action="store_true", help="Use pip package manager instead of uv"
    )

    # Common arguments for all commands
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    return parser.parse_args()


def load_targets(targets_path: str) -> list[CrawlTarget]:
    """Load crawl targets from file."""
    if not os.path.exists(targets_path):
        raise FileNotFoundError(f"Targets file not found: {targets_path}")

    with open(targets_path) as f:
        if targets_path.endswith(".json"):
            targets_data = json.load(f)
        elif targets_path.endswith(".yaml") or targets_path.endswith(".yml"):
            targets_data = yaml.safe_load(f)
        else:
            raise ValueError("Targets file must be JSON or YAML")

    return [CrawlTarget(**target) for target in targets_data]


def run_server():
    """Run the FastAPI web server."""
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)


async def run_benchmark(args) -> None:
    """Run benchmark command."""
    # Parse URLs
    urls = [url.strip() for url in args.urls.split(",")]

    # Parse backends
    backends = args.backends.split(",") if args.backends != "all" else "all"

    # Create benchmark instance
    benchmark = BackendBenchmark()

    # Register backends
    if backends == "all":
        benchmark.register_all_available_backends()
    else:
        # Register specific backends
        for backend_name in backends:
            if backend_name == "http":
                from .backends.http_backend import HTTPBackend, HTTPBackendConfig

                http_backend = HTTPBackend(config=HTTPBackendConfig())
                benchmark.register_backend(http_backend)
            elif backend_name == "crawl4ai":
                from .backends.crawl4ai_backend import Crawl4AIBackend, Crawl4AIConfig

                crawl4ai_backend = Crawl4AIBackend(config=Crawl4AIConfig())
                benchmark.register_backend(crawl4ai_backend)
            elif backend_name == "lightpanda":
                from .backends.lightpanda_backend import (
                    LightpandaBackend,
                    LightpandaConfig,
                )

                lightpanda_backend = LightpandaBackend(config=LightpandaConfig())
                benchmark.register_backend(lightpanda_backend)
            elif backend_name == "file":
                from .backends.file_backend import FileBackend

                file_backend = FileBackend()
                benchmark.register_backend(file_backend)

    # Run benchmark
    logging.info(
        f"Running benchmark on {len(urls)} URLs with {len(benchmark.backends)} backends"
    )
    for url in urls:
        logging.info(f"Benchmarking URL: {url}")
        results = await benchmark.benchmark_url(url)

        # Log results
        for backend_name, result in results.items():
            if result.success:
                logging.info(
                    f"  {backend_name}: Success, {result.crawl_time:.2f}s, {result.content_size} bytes"
                )
            else:
                logging.info(f"  {backend_name}: Failed, {result.error}")

    # Generate report
    output_file = (
        args.output or f"benchmark_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    )
    benchmark.generate_report(output_file)
    logging.info(f"Benchmark report saved to {output_file}")

    # Close backends
    await benchmark.close()


def main() -> None:
    """Main entry point."""
    args = parse_args()

    try:
        # Setup logging
        log_level = "DEBUG" if getattr(args, "verbose", False) else "INFO"
        setup_logging(level=log_level)

        # Handle commands
        if args.command == "scrape":
            # Load configuration
            config = load_config(args.config)

            # Load targets
            targets = load_targets(args.targets)

            # Run as standard CLI crawler
            logging.info("Running with standard crawler")
            crawler = setup_crawler(config)
            asyncio.run(run_crawler(crawler, targets))

        elif args.command == "serve":
            # Run as web server
            import uvicorn

            uvicorn.run(app, host=args.host, port=args.port)

        elif args.command == "benchmark":
            # Run benchmark
            asyncio.run(run_benchmark(args))

        else:
            logging.error(f"Unknown command: {args.command}")

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        raise


if __name__ == "__main__":
    main()
