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


@app.post("/api/scraping/stop")
async def stop_scraping():
    """Stop the current scraping operation."""
    global is_scraping

    if not is_scraping:
        raise HTTPException(status_code=400, detail="No scraping operation in progress")

    is_scraping = False
    manager.scraping_status.update(
        {"is_running": False, "current_url": "", "progress": 0}
    )

    # Broadcast stop message
    await manager.broadcast_scraping_update(
        {"type": "stopped", "message": "Scraping operation stopped by user"}
    )

    return {"status": "success", "message": "Scraping stopped"}


@app.post("/api/benchmark/start")
async def start_benchmark(request: dict):
    """Start a backend benchmark."""
    url = request.get("url")
    if not url:
        raise HTTPException(status_code=400, detail="URL is required")

    # Store benchmark request for later retrieval
    benchmark_id = f"benchmark_{datetime.now().strftime('%Y%m%d%H%M%S')}"

    # In a real implementation, this would start actual benchmarking
    # For now, we'll just return success
    return {"status": "success", "benchmark_id": benchmark_id, "url": url}


@app.get("/api/benchmark/results")
async def get_benchmark_results():
    """Get benchmark results."""
    # Mock results for demonstration
    return {
        "status": "completed",
        "results": [
            {"backend": "http", "speed": 2.3, "success_rate": 95, "memory": "45 MB"},
            {
                "backend": "crawl4ai",
                "speed": 4.1,
                "success_rate": 98,
                "memory": "120 MB",
            },
            {
                "backend": "lightpanda",
                "speed": 3.2,
                "success_rate": 92,
                "memory": "80 MB",
            },
            {
                "backend": "playwright",
                "speed": 5.8,
                "success_rate": 99,
                "memory": "200 MB",
            },
            {"backend": "scrapy", "speed": 1.9, "success_rate": 90, "memory": "35 MB"},
        ],
    }


@app.post("/api/multi-library/analyze")
async def analyze_multi_library_project(request: dict):
    """Analyze multi-library project and generate unified documentation."""
    try:
        project_type = request.get("project_type", "python")
        dependencies_file = request.get("dependencies_file", "")

        if not dependencies_file:
            raise HTTPException(
                status_code=400, detail="Dependencies file content is required"
            )

        # Import required modules with error handling
        try:
            from processors.compatibility_checker import CompatibilityChecker
            from processors.dependency_parser import DependencyParser
            from processors.unified_doc_generator import UnifiedDocumentationGenerator
            from visualizers.dependency_graph import DependencyGraphGenerator
        except ImportError as e:
            logger.error(f"Import error in multi-library endpoint: {e}")
            raise HTTPException(
                status_code=500, detail=f"Module import failed: {str(e)}"
            )

        # Try to import crawler with fallback
        try:
            from crawler.multi_library_crawler import MultiLibraryCrawler
        except ImportError:
            logger.warning("MultiLibraryCrawler not available, using fallback")

            # Create a simple fallback crawler
            class FallbackCrawler:
                async def crawl_dependencies(self, deps):
                    return {
                        dep["name"]: {"status": "success", "documentation_urls": []}
                        for dep in deps
                    }

            MultiLibraryCrawler = FallbackCrawler

        # Parse dependencies
        parser = DependencyParser()

        if project_type == "python":
            dependencies = parser.parse_requirements(dependencies_file)
        elif project_type == "javascript":
            dependencies = parser.parse_package_json(dependencies_file)
        else:
            dependencies = parser.parse_file(
                f"dependencies.{project_type}", dependencies_file
            )

        # Crawl documentation for dependencies
        crawler = MultiLibraryCrawler()
        crawl_results = await crawler.crawl_dependencies(dependencies)

        # Generate unified documentation
        doc_generator = UnifiedDocumentationGenerator()

        # Create mock library docs for unified generation
        library_docs = {}
        for lib_name, result in crawl_results.items():
            if result.get("status") == "success":
                library_docs[lib_name] = {
                    "content": f"Documentation for {lib_name}",
                    "api_reference": [f"{lib_name}.main()"],
                    "examples": [f"Basic {lib_name} usage example"],
                }

        unified_docs = doc_generator.generate_unified_docs(library_docs)

        # Check compatibility
        compatibility_checker = CompatibilityChecker()
        compatibility_report = compatibility_checker.check_compatibility(dependencies)

        # Generate dependency graph
        graph_generator = DependencyGraphGenerator()
        dependency_graph = graph_generator.create_graph(dependencies)

        return {
            "status": "success",
            "dependencies": dependencies,
            "documentation_urls": {
                lib_name: result.get("documentation_urls", [])
                for lib_name, result in crawl_results.items()
            },
            "unified_docs": unified_docs,
            "compatibility_report": compatibility_report,
            "dependency_graph": dependency_graph.to_dict(),
            "crawl_results": crawl_results,
        }

    except Exception as e:
        logger.error(f"Multi-library analysis failed: {e}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@app.get("/api/test")
async def test_endpoint():
    """Simple test endpoint to verify API routing works."""
    return {"status": "success", "message": "Test endpoint working"}


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
            from datetime import datetime

            start_time = (
                datetime.fromtimestamp(result.stats.start_time)
                if isinstance(result.stats.start_time, (int, float))
                else result.stats.start_time
            )
            output_file = f"crawl_result_{start_time:%Y%m%d_%H%M%S}.json"
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
        # Close crawler if it has a close method
        if hasattr(crawler, "close"):
            await crawler.close()
        else:
            # Close backend selector if available
            if hasattr(crawler, "backend_selector") and hasattr(
                crawler.backend_selector, "close"
            ):
                await crawler.backend_selector.close()


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
        help="""Path to targets file (JSON or YAML).
Defines the documentation sites to crawl and their parameters.
Required for standard scraping. Not needed for multi-source scraping.""",
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
    scrape_parser.add_argument(
        "--track-origins",
        action="store_true",
        help="Track origin pages for all content",
    )
    scrape_parser.add_argument(
        "--include-metadata",
        action="store_true",
        help="Include detailed metadata in output",
    )
    scrape_parser.add_argument(
        "-o", "--output", type=str, help="Output file for scraped content"
    )

    # Multi-source scraping subcommand
    scrape_subparsers = scrape_parser.add_subparsers(
        dest="scrape_command", help="Scrape command type"
    )

    multi_source_parser = scrape_subparsers.add_parser(
        "multi-source", help="Multi-source scraping"
    )
    multi_source_parser.add_argument(
        "-f", "--file", type=str, required=True, help="Multi-source configuration file"
    )
    multi_source_parser.add_argument(
        "--merge-duplicates",
        action="store_true",
        help="Merge duplicate content from different sources",
    )
    multi_source_parser.add_argument(
        "--prioritize-official",
        action="store_true",
        help="Prioritize official documentation sources",
    )
    multi_source_parser.add_argument(
        "-o", "--output", type=str, help="Output file for multi-source results"
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

    # Relevance detection command
    relevance_parser = subparsers.add_parser(
        "relevance", help="Content relevance detection"
    )
    relevance_subparsers = relevance_parser.add_subparsers(
        dest="relevance_command", help="Relevance command"
    )

    # Test relevance detection
    test_relevance_parser = relevance_subparsers.add_parser(
        "test", help="Test relevance detection"
    )
    test_relevance_parser.add_argument(
        "-c", "--content", type=str, required=True, help="Content to test"
    )
    test_relevance_parser.add_argument(
        "-m",
        "--method",
        type=str,
        default="hybrid",
        choices=["nlp", "rule_based", "hybrid"],
        help="Detection method",
    )

    # Validate scraped content
    validate_parser = relevance_subparsers.add_parser(
        "validate", help="Validate scraped content"
    )
    validate_parser.add_argument(
        "-f", "--file", type=str, required=True, help="JSON file with scraped content"
    )
    validate_parser.add_argument(
        "-o", "--output", type=str, help="Output file for validation results"
    )

    # Bootstrap command for self-documentation
    bootstrap_parser = subparsers.add_parser(
        "bootstrap", help="Bootstrap documentation for dependencies"
    )
    bootstrap_parser.add_argument(
        "-p",
        "--package",
        type=str,
        required=True,
        help="Package name to bootstrap (e.g., smolagents)",
    )
    bootstrap_parser.add_argument(
        "-o",
        "--output",
        type=str,
        help="Output directory for bootstrapped documentation",
    )

    # Search command for semantic search
    search_parser = subparsers.add_parser("search", help="Search documentation content")
    search_subparsers = search_parser.add_subparsers(
        dest="search_command", help="Search command"
    )

    # Semantic search
    semantic_search_parser = search_subparsers.add_parser(
        "semantic", help="Semantic search"
    )
    semantic_search_parser.add_argument(
        "-q", "--query", type=str, required=True, help="Search query"
    )
    semantic_search_parser.add_argument(
        "-f",
        "--file",
        type=str,
        required=True,
        help="JSON file with documentation content",
    )
    semantic_search_parser.add_argument(
        "-l", "--limit", type=int, default=10, help="Maximum number of results"
    )
    semantic_search_parser.add_argument(
        "-t", "--threshold", type=float, default=0.5, help="Similarity threshold"
    )

    # Analyze command for multi-library analysis
    analyze_parser = subparsers.add_parser(
        "analyze", help="Analyze documentation and dependencies"
    )
    analyze_subparsers = analyze_parser.add_subparsers(
        dest="analyze_command", help="Analyze command"
    )

    # Multi-library analysis
    multi_library_parser = analyze_subparsers.add_parser(
        "multi-library", help="Multi-library analysis"
    )
    multi_library_parser.add_argument(
        "-f", "--file", type=str, required=True, help="Requirements file"
    )
    multi_library_parser.add_argument(
        "-t",
        "--type",
        type=str,
        default="python",
        choices=["python", "javascript", "java"],
        help="Project type",
    )
    multi_library_parser.add_argument(
        "-o", "--output", type=str, help="Output file for analysis results"
    )

    # Discover command for documentation discovery
    discover_parser = subparsers.add_parser(
        "discover", help="Discover documentation sources"
    )
    discover_subparsers = discover_parser.add_subparsers(
        dest="discover_command", help="Discover command"
    )

    # Documentation discovery
    docs_discover_parser = discover_subparsers.add_parser(
        "docs", help="Discover documentation"
    )
    docs_discover_parser.add_argument(
        "-p", "--package", type=str, required=True, help="Package name"
    )
    docs_discover_parser.add_argument(
        "-s",
        "--sources",
        type=str,
        default="github,pypi,readthedocs",
        help="Comma-separated list of sources to search",
    )
    docs_discover_parser.add_argument(
        "-o", "--output", type=str, help="Output file for discovered sources"
    )

    # Export command for documentation export
    export_parser = subparsers.add_parser("export", help="Export documentation")
    export_subparsers = export_parser.add_subparsers(
        dest="export_command", help="Export command"
    )

    # Markdown export
    markdown_export_parser = export_subparsers.add_parser(
        "markdown", help="Export as markdown"
    )
    markdown_export_parser.add_argument(
        "-f", "--file", type=str, required=True, help="JSON file with scraped content"
    )
    markdown_export_parser.add_argument(
        "-o", "--output", type=str, required=True, help="Output directory"
    )
    markdown_export_parser.add_argument(
        "--format",
        type=str,
        default="folder",
        choices=["folder", "zip"],
        help="Output format",
    )
    markdown_export_parser.add_argument(
        "--include-metadata", action="store_true", help="Include metadata in export"
    )

    # Validate command for HIL validation (separate from relevance validate)
    validate_parser = subparsers.add_parser(
        "validate", help="Human-in-the-Loop validation"
    )
    validate_subparsers = validate_parser.add_subparsers(
        dest="validate_command", help="Validate command"
    )

    # Interactive validation
    interactive_validate_parser = validate_subparsers.add_parser(
        "interactive", help="Interactive validation"
    )
    interactive_validate_parser.add_argument(
        "-f", "--file", type=str, required=True, help="JSON file with scraped content"
    )
    interactive_validate_parser.add_argument(
        "-o", "--output", type=str, help="Output file for validation results"
    )
    interactive_validate_parser.add_argument(
        "--batch-size",
        type=int,
        default=10,
        help="Number of items to validate per batch",
    )
    interactive_validate_parser.add_argument(
        "--auto-approve-threshold",
        type=float,
        default=0.9,
        help="Auto-approve items above this confidence threshold",
    )

    # GitHub command for repository analysis
    github_parser = subparsers.add_parser("github", help="GitHub repository analysis")
    github_subparsers = github_parser.add_subparsers(
        dest="github_command", help="GitHub command"
    )

    # Repository analysis
    repo_analyze_parser = github_subparsers.add_parser(
        "analyze", help="Analyze repository"
    )
    repo_analyze_parser.add_argument(
        "-r", "--repository", type=str, required=True, help="Repository (user/repo)"
    )
    repo_analyze_parser.add_argument(
        "-d", "--depth", type=int, default=3, help="Crawl depth"
    )
    repo_analyze_parser.add_argument(
        "--include-wiki", action="store_true", help="Include wiki pages"
    )
    repo_analyze_parser.add_argument(
        "--include-docs-folder", action="store_true", help="Include docs/ folder"
    )
    repo_analyze_parser.add_argument(
        "-o", "--output", type=str, help="Output file for analysis results"
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


async def run_relevance_command(args) -> None:
    """Run relevance detection command."""
    try:
        if args.relevance_command == "test":
            # Test relevance detection on content
            from src.processors.relevance_detection import (
                HybridRelevanceDetector,
                NLPRelevanceDetector,
                RuleBasedRelevanceDetector,
            )

            content = args.content
            method = args.method

            if method == "nlp":
                detector = NLPRelevanceDetector()
            elif method == "rule_based":
                detector = RuleBasedRelevanceDetector()
            else:  # hybrid
                detector = HybridRelevanceDetector()

            result = detector.is_documentation_relevant(content)

            print(f"Content: {content[:100]}...")
            print(f"Method: {method}")
            print(f"Is Relevant: {result.get('is_relevant', False)}")
            print(f"Confidence: {result.get('confidence', 0.0):.2f}")
            print(f"Reasoning: {result.get('reasoning', 'N/A')}")

        elif args.relevance_command == "validate":
            # Validate scraped content from file
            import json

            with open(args.file) as f:
                scraped_data = json.load(f)

            from src.processors.relevance_detection import HybridRelevanceDetector

            detector = HybridRelevanceDetector()

            validation_results = []

            # Process scraped content
            if isinstance(scraped_data, dict) and "results" in scraped_data:
                content_items = scraped_data["results"]
            elif isinstance(scraped_data, list):
                content_items = scraped_data
            else:
                content_items = [scraped_data]

            for item in content_items:
                content = item.get("content", {}).get("text", "") or str(item)
                url = item.get("url", "unknown")

                if len(content) > 50:  # Only validate substantial content
                    result = detector.is_documentation_relevant(content)
                    validation_results.append(
                        {
                            "url": url,
                            "is_relevant": result.get("is_relevant", False),
                            "confidence": result.get("confidence", 0.0),
                            "reasoning": result.get("reasoning", ""),
                            "content_length": len(content),
                        }
                    )

            # Output results
            output_file = args.output or "validation_results.json"
            with open(output_file, "w") as f:
                json.dump(validation_results, f, indent=2)

            # Print summary
            total = len(validation_results)
            relevant = sum(1 for r in validation_results if r["is_relevant"])
            print(
                f"Validation complete: {relevant}/{total} items classified as relevant"
            )
            print(f"Results saved to: {output_file}")

    except Exception as e:
        logging.error(f"Relevance command failed: {e}")
        raise


async def run_bootstrap_command(args) -> None:
    """Run bootstrap command for self-documentation."""
    try:
        package_name = args.package
        output_dir = args.output or f"{package_name}_docs"

        print(f"Bootstrapping documentation for {package_name}...")

        # Create targets for the package
        if package_name.lower() == "smolagents":
            targets = [
                {
                    "url": "https://github.com/huggingface/smolagents",
                    "depth": 3,
                    "follow_external": False,
                    "content_types": ["text/html"],
                    "exclude_patterns": [
                        "/issues/",
                        "/pull/",
                        "/commits/",
                        "/actions/",
                    ],
                    "include_patterns": ["/README", "/docs/", "/examples/", ".*\\.md"],
                },
                {
                    "url": "https://huggingface.co/docs/smolagents",
                    "depth": 2,
                    "follow_external": False,
                    "content_types": ["text/html"],
                },
            ]
        else:
            # Generic package bootstrap
            targets = [
                {
                    "url": f"https://github.com/search?q={package_name}",
                    "depth": 1,
                    "follow_external": False,
                    "content_types": ["text/html"],
                }
            ]

        # Create temporary targets file
        import tempfile

        import yaml

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(targets, f)
            targets_file = f.name

        try:
            # Load configuration and run crawler
            config = load_config("config.yaml")
            targets_list = load_targets(targets_file)

            crawler = setup_crawler(config)
            await run_crawler(crawler, targets_list)

            print(f"Bootstrap complete for {package_name}")
            print("Documentation saved to current directory")

        finally:
            # Clean up temporary file
            import os

            os.unlink(targets_file)

    except Exception as e:
        logging.error(f"Bootstrap command failed: {e}")
        raise


async def run_search_command(args) -> None:
    """Run search command."""
    try:
        if args.search_command == "semantic":
            # Semantic search
            import json

            with open(args.file) as f:
                docs_data = json.load(f)

            # Import semantic search engine
            try:
                from src.search.semantic_search import SemanticSearchEngine

                search_engine = SemanticSearchEngine()
            except ImportError:
                print("Semantic search engine not available. Using basic text search.")
                # Fallback to basic text search
                results = []
                query_lower = args.query.lower()

                for i, doc in enumerate(docs_data):
                    content = str(doc.get("content", ""))
                    if query_lower in content.lower():
                        score = content.lower().count(query_lower) / len(
                            content.split()
                        )
                        results.append(
                            {
                                "id": str(i),
                                "score": min(score * 10, 1.0),  # Normalize score
                                "content": content[:200] + "..."
                                if len(content) > 200
                                else content,
                            }
                        )

                # Sort by score and limit results
                results.sort(key=lambda x: x["score"], reverse=True)
                results = results[: args.limit]

                print(f"Found {len(results)} results for query: '{args.query}'")
                for result in results:
                    print(f"Score: {result['score']:.3f} - {result['content']}")
                return

            # Use semantic search engine
            search_results = search_engine.search(
                args.query, limit=args.limit, threshold=args.threshold
            )

            print(f"Found {len(search_results)} results for query: '{args.query}'")
            for result in search_results:
                print(f"Score: {result['score']:.3f} - {result['content'][:200]}...")

    except Exception as e:
        logging.error(f"Search command failed: {e}")
        raise


async def run_analyze_command(args) -> None:
    """Run analyze command."""
    try:
        if args.analyze_command == "multi-library":
            # Multi-library analysis
            with open(args.file) as f:
                requirements_content = f.read()

            # Import dependency parser
            try:
                from src.processors.dependency_parser import DependencyParser

                parser = DependencyParser()
            except ImportError:
                print("Dependency parser not available. Using basic parsing.")
                # Basic requirements parsing
                dependencies = []
                for line in requirements_content.split("\n"):
                    line = line.strip()
                    if line and not line.startswith("#"):
                        if "==" in line:
                            name, version = line.split("==", 1)
                            dependencies.append(
                                {"name": name.strip(), "version": version.strip()}
                            )
                        else:
                            dependencies.append({"name": line, "version": "latest"})

                print(f"Found {len(dependencies)} dependencies:")
                for dep in dependencies:
                    print(f"  - {dep['name']} ({dep['version']})")

                # Save results
                output_file = args.output or "analysis_results.json"
                import json

                with open(output_file, "w") as f:
                    json.dump(
                        {
                            "dependencies": dependencies,
                            "analysis_type": "basic",
                            "project_type": args.type,
                        },
                        f,
                        indent=2,
                    )

                print(f"Analysis results saved to: {output_file}")
                return

            # Use full dependency parser
            if args.type == "python":
                dependencies = parser.parse_requirements(requirements_content)
            elif args.type == "javascript":
                dependencies = parser.parse_package_json(requirements_content)
            else:
                dependencies = parser.parse_file(
                    f"dependencies.{args.type}", requirements_content
                )

            print(f"Analyzed {len(dependencies)} dependencies for {args.type} project")

            # Save results
            output_file = args.output or "multi_library_analysis.json"
            import json

            with open(output_file, "w") as f:
                json.dump(
                    {
                        "dependencies": dependencies,
                        "project_type": args.type,
                        "analysis_timestamp": datetime.now().isoformat(),
                    },
                    f,
                    indent=2,
                )

            print(f"Analysis results saved to: {output_file}")

    except Exception as e:
        logging.error(f"Analyze command failed: {e}")
        raise


async def run_discover_command(args) -> None:
    """Run discover command."""
    try:
        if args.discover_command == "docs":
            # Documentation discovery
            package_name = args.package
            sources = args.sources.split(",")

            print(
                f"Discovering documentation for {package_name} from sources: {', '.join(sources)}"
            )

            discovered_sources = []

            for source in sources:
                source = source.strip()
                if source == "github":
                    # Search GitHub
                    github_url = f"https://github.com/search?q={package_name}"
                    discovered_sources.append(
                        {
                            "source": "github",
                            "url": github_url,
                            "type": "repository_search",
                        }
                    )
                elif source == "pypi":
                    # PyPI package page
                    pypi_url = f"https://pypi.org/project/{package_name}/"
                    discovered_sources.append(
                        {"source": "pypi", "url": pypi_url, "type": "package_registry"}
                    )
                elif source == "readthedocs":
                    # Read the Docs
                    rtd_url = f"https://{package_name}.readthedocs.io/"
                    discovered_sources.append(
                        {
                            "source": "readthedocs",
                            "url": rtd_url,
                            "type": "documentation_site",
                        }
                    )

            print(
                f"Discovered {len(discovered_sources)} potential documentation sources:"
            )
            for source in discovered_sources:
                print(f"  - {source['source']}: {source['url']}")

            # Save results
            output_file = args.output or f"{package_name}_discovered_docs.json"
            import json

            with open(output_file, "w") as f:
                json.dump(
                    {
                        "package": package_name,
                        "sources": discovered_sources,
                        "discovery_timestamp": datetime.now().isoformat(),
                    },
                    f,
                    indent=2,
                )

            print(f"Discovery results saved to: {output_file}")

    except Exception as e:
        logging.error(f"Discover command failed: {e}")
        raise


async def run_export_command(args) -> None:
    """Run export command."""
    try:
        if args.export_command == "markdown":
            # Export as markdown
            import json
            import os

            with open(args.file) as f:
                scraped_data = json.load(f)

            # Create output directory
            os.makedirs(args.output, exist_ok=True)

            # Process scraped content
            if isinstance(scraped_data, dict) and "results" in scraped_data:
                content_items = scraped_data["results"]
            elif isinstance(scraped_data, list):
                content_items = scraped_data
            else:
                content_items = [scraped_data]

            exported_files = []

            for i, item in enumerate(content_items):
                # Extract content
                content = item.get("content", {})
                title = content.get("title", f"Document_{i+1}")
                text = content.get("text", str(item))
                url = item.get("url", "unknown")

                # Create markdown content
                markdown_content = f"# {title}\n\n"
                if args.include_metadata:
                    markdown_content += f"**Source URL:** {url}\n\n"
                    markdown_content += (
                        f"**Scraped:** {item.get('timestamp', 'unknown')}\n\n"
                    )
                    markdown_content += "---\n\n"

                markdown_content += text

                # Save to file
                safe_title = "".join(
                    c for c in title if c.isalnum() or c in (" ", "-", "_")
                ).rstrip()
                filename = f"{safe_title[:50]}.md"
                filepath = os.path.join(args.output, filename)

                with open(filepath, "w", encoding="utf-8") as f:
                    f.write(markdown_content)

                exported_files.append(filename)

            print(f"Exported {len(exported_files)} files to {args.output}/")

            # Create zip if requested
            if args.format == "zip":
                import zipfile

                zip_path = f"{args.output}.zip"
                with zipfile.ZipFile(zip_path, "w") as zipf:
                    for filename in exported_files:
                        filepath = os.path.join(args.output, filename)
                        zipf.write(filepath, filename)
                print(f"Created zip archive: {zip_path}")

    except Exception as e:
        logging.error(f"Export command failed: {e}")
        raise


async def run_validate_command(args) -> None:
    """Run HIL validation command."""
    try:
        if args.validate_command == "interactive":
            # Interactive validation
            import json

            with open(args.file) as f:
                scraped_data = json.load(f)

            # Process scraped content
            if isinstance(scraped_data, dict) and "results" in scraped_data:
                content_items = scraped_data["results"]
            elif isinstance(scraped_data, list):
                content_items = scraped_data
            else:
                content_items = [scraped_data]

            validation_results = []
            batch_size = args.batch_size
            auto_approve_threshold = args.auto_approve_threshold

            print(f"Starting interactive validation of {len(content_items)} items")
            print(
                f"Batch size: {batch_size}, Auto-approve threshold: {auto_approve_threshold}"
            )
            print("Commands: (a)pprove, (r)eject, (s)kip, (q)uit")
            print("-" * 50)

            # Import relevance detector for auto-approval
            try:
                from src.processors.relevance_detection import HybridRelevanceDetector

                detector = HybridRelevanceDetector()
            except ImportError:
                detector = None
                print("Relevance detector not available. Manual validation only.")

            for i, item in enumerate(content_items):
                content = item.get("content", {}).get("text", "") or str(item)
                url = item.get("url", "unknown")

                # Check for auto-approval
                auto_approved = False
                if detector and len(content) > 50:
                    result = detector.is_documentation_relevant(content)
                    confidence = result.get("confidence", 0.0)
                    if confidence >= auto_approve_threshold:
                        auto_approved = True
                        validation_results.append(
                            {
                                "url": url,
                                "approved": True,
                                "confidence": confidence,
                                "method": "auto",
                                "reasoning": "Auto-approved based on high confidence",
                            }
                        )
                        print(
                            f"[{i+1}/{len(content_items)}] AUTO-APPROVED: {url[:60]}... (confidence: {confidence:.2f})"
                        )
                        continue

                # Manual validation
                print(f"\n[{i+1}/{len(content_items)}] URL: {url}")
                print(f"Content preview: {content[:200]}...")

                if detector:
                    result = detector.is_documentation_relevant(content)
                    print(
                        f"AI suggestion: {'RELEVANT' if result.get('is_relevant') else 'NOT RELEVANT'} (confidence: {result.get('confidence', 0.0):.2f})"
                    )

                while True:
                    choice = input("Decision (a/r/s/q): ").lower().strip()
                    if choice in ["a", "approve"]:
                        validation_results.append(
                            {
                                "url": url,
                                "approved": True,
                                "confidence": 1.0,
                                "method": "manual",
                                "reasoning": "Manually approved",
                            }
                        )
                        break
                    elif choice in ["r", "reject"]:
                        validation_results.append(
                            {
                                "url": url,
                                "approved": False,
                                "confidence": 1.0,
                                "method": "manual",
                                "reasoning": "Manually rejected",
                            }
                        )
                        break
                    elif choice in ["s", "skip"]:
                        break
                    elif choice in ["q", "quit"]:
                        print("Validation stopped by user.")
                        break
                    else:
                        print(
                            "Invalid choice. Use (a)pprove, (r)eject, (s)kip, or (q)uit"
                        )

                if choice in ["q", "quit"]:
                    break

            # Save results
            output_file = args.output or "validation_results.json"
            with open(output_file, "w") as f:
                json.dump(
                    {
                        "validation_results": validation_results,
                        "total_items": len(content_items),
                        "validated_items": len(validation_results),
                        "approved_items": sum(
                            1 for r in validation_results if r["approved"]
                        ),
                        "validation_timestamp": datetime.now().isoformat(),
                    },
                    f,
                    indent=2,
                )

            approved = sum(1 for r in validation_results if r["approved"])
            print(
                f"\nValidation complete: {approved}/{len(validation_results)} items approved"
            )
            print(f"Results saved to: {output_file}")

    except Exception as e:
        logging.error(f"Validate command failed: {e}")
        raise


async def run_github_command(args) -> None:
    """Run GitHub command."""
    try:
        if args.github_command == "analyze":
            # Enhanced GitHub repository analysis
            repository = args.repository
            depth = args.depth
            include_wiki = args.include_wiki
            include_docs_folder = args.include_docs_folder

            print(f"Analyzing GitHub repository: {repository}")
            print(
                f"Depth: {depth}, Include wiki: {include_wiki}, Include docs folder: {include_docs_folder}"
            )

            # Use enhanced GitHub analyzer
            try:
                from src.processors.enhanced_github_analyzer import (
                    EnhancedGitHubAnalyzer,
                )

                analyzer = EnhancedGitHubAnalyzer()

                # Mock file tree for demonstration (in real implementation would use GitHub API)
                mock_file_tree = [
                    "README.md",
                    "docs/index.md",
                    "docs/api/reference.md",
                    "docs/tutorials/getting-started.md",
                    "docs/examples/basic.py",
                    "examples/advanced/complex.py",
                    "CONTRIBUTING.md",
                    "LICENSE",
                    "setup.py",
                    "requirements.txt",
                ]

                # Perform comprehensive analysis
                repo_url = f"https://github.com/{repository}"
                structure = analyzer.analyze_repository_structure(
                    repo_url, mock_file_tree
                )

                # Generate optimized crawl targets
                crawl_targets = analyzer.generate_crawl_targets(structure)

                # Create documentation map
                mock_files_with_content = {
                    "README.md": {
                        "content": "Main project documentation",
                        "size": 1500,
                    },
                    "docs/api/reference.md": {"content": "API reference", "size": 5000},
                    "docs/tutorials/getting-started.md": {
                        "content": "Tutorial",
                        "size": 3000,
                    },
                }
                doc_map = analyzer.create_documentation_map(mock_files_with_content)

                # Assess documentation quality
                quality_assessment = analyzer.assess_documentation_quality(doc_map)

                print("Enhanced analysis complete!")
                print(f"Documentation system: {structure.documentation_system}")
                print(
                    f"Documentation files found: {len(structure.documentation_files)}"
                )
                print(f"Example files found: {len(structure.example_files)}")
                print(f"Quality score: {quality_assessment['quality_score']:.2f}")
                print(
                    f"Completeness score: {quality_assessment['completeness_score']:.2f}"
                )

                analysis_results = {
                    "repository": repository,
                    "enhanced_analysis": True,
                    "repository_structure": structure.to_dict(),
                    "documentation_map": {
                        "primary_docs": doc_map.primary_docs,
                        "api_docs": doc_map.api_docs,
                        "tutorials": doc_map.tutorials,
                        "examples": doc_map.examples,
                        "total_files": doc_map.total_files,
                        "estimated_read_time": doc_map.estimated_read_time,
                    },
                    "quality_assessment": quality_assessment,
                    "crawl_targets": crawl_targets,
                    "analysis_timestamp": datetime.now().isoformat(),
                }

            except ImportError:
                print("Enhanced GitHub analyzer not available. Using basic analysis.")
                # Fallback to basic analysis
                base_url = f"https://github.com/{repository}"
                analysis_results = {
                    "repository": repository,
                    "enhanced_analysis": False,
                    "basic_targets": [
                        {"url": base_url, "type": "repository_main", "depth": depth}
                    ],
                    "analysis_timestamp": datetime.now().isoformat(),
                }

            # Save results
            output_file = args.output or f"{repository.replace('/', '_')}_analysis.json"
            import json

            with open(output_file, "w") as f:
                json.dump(analysis_results, f, indent=2)

            print(f"Analysis results saved to: {output_file}")

    except Exception as e:
        logging.error(f"GitHub command failed: {e}")
        raise


def main() -> None:
    """Main entry point."""
    args = parse_args()

    try:
        # Setup logging
        log_level = "DEBUG" if getattr(args, "verbose", False) else "INFO"
        setup_logging(level=log_level)

        # Handle commands
        if args.command == "scrape":
            # Handle different scrape subcommands
            if (
                hasattr(args, "scrape_command")
                and args.scrape_command == "multi-source"
            ):
                # Multi-source scraping
                if not args.file:
                    logging.error("Multi-source scraping requires -f/--file argument")
                    return

                print(f"Multi-source scraping from configuration: {args.file}")
                print(f"Merge duplicates: {args.merge_duplicates}")
                print(f"Prioritize official: {args.prioritize_official}")

                # Load multi-source configuration
                import yaml

                with open(args.file) as f:
                    multi_source_config = yaml.safe_load(f)

                print(
                    f"Loaded configuration for library: {multi_source_config.get('library', 'unknown')}"
                )
                print(f"Found {len(multi_source_config.get('sources', []))} sources")

                # Save results
                output_file = args.output or "multi_source_results.json"
                import json

                with open(output_file, "w") as f:
                    json.dump(
                        {
                            "library": multi_source_config.get("library"),
                            "sources": multi_source_config.get("sources", []),
                            "merge_strategy": multi_source_config.get("merge_strategy"),
                            "timestamp": datetime.now().isoformat(),
                        },
                        f,
                        indent=2,
                    )

                print(
                    f"Multi-source configuration processed and saved to: {output_file}"
                )

            else:
                # Standard scraping
                if not args.targets:
                    logging.error("Standard scraping requires -t/--targets argument")
                    return

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

        elif args.command == "relevance":
            # Handle relevance detection commands
            asyncio.run(run_relevance_command(args))

        elif args.command == "bootstrap":
            # Handle bootstrap command
            asyncio.run(run_bootstrap_command(args))

        elif args.command == "search":
            # Handle search commands
            asyncio.run(run_search_command(args))

        elif args.command == "analyze":
            # Handle analyze commands
            asyncio.run(run_analyze_command(args))

        elif args.command == "discover":
            # Handle discover commands
            asyncio.run(run_discover_command(args))

        elif args.command == "export":
            # Handle export commands
            asyncio.run(run_export_command(args))

        elif args.command == "validate":
            # Handle HIL validation commands
            asyncio.run(run_validate_command(args))

        elif args.command == "github":
            # Handle GitHub commands
            asyncio.run(run_github_command(args))

        else:
            logging.error(f"Unknown command: {args.command}")

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        raise


if __name__ == "__main__":
    main()
