#!/usr/bin/env python3
import argparse
import asyncio
import json
import logging
import os
from typing import Any, Dict, Optional, List, Union
from datetime import datetime
from pathlib import Path
import re

import yaml
from pydantic import BaseModel
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect, HTTPException, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import subprocess

from .backends.crawl4ai import Crawl4AIBackend, Crawl4AIConfig
from .backends.selector import BackendCriteria, BackendSelector
from .backends.lightpanda_backend import LightpandaBackend, LightpandaConfig
from .crawler import CrawlerConfig, CrawlTarget, DocumentationCrawler
from .organizers.doc_organizer import DocumentOrganizer, OrganizationConfig
from .organizers.library_version_tracker import LibraryVersionTracker, LibraryRegistry
from .processors.content_processor import ContentProcessor
from .processors.content.models import ProcessorConfig as ProcessingConfig
from .processors.quality_checker import QualityChecker, QualityConfig
from .utils.helpers import setup_logging
from .utils.doc_site_verifier import DocSiteVerifier
from .backends.base import CrawlResult
from .backends.file_backend import FileBackend
from .benchmarking.backend_benchmark import BackendBenchmark
from .utils.package_manager import PackageManager, PackageManagerConfig
from .visualizers.version_history import VersionHistoryVisualizer
from .processors.nlp.categorizer import DocumentCategorizer
from .processors.nlp.topic_modeling import TopicModeler
from .crawler.distributed.manager import DistributedCrawlManager
from .crawler.distributed.worker import CrawlWorker
from .crawler.distributed.models import DistributedConfig, WorkerTask
from .crawler.distributed.runner import DistributedCrawlRunner

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# In-memory storage for web interface
scraping_results_storage: Dict[str, Dict] = {}
active_scraper = None
is_scraping = False
library_operations: Dict[str, Dict] = {}

class AppConfig(BaseModel):
    """Application configuration model."""
    crawler: CrawlerConfig
    processing: ProcessingConfig
    quality: QualityConfig
    organization: OrganizationConfig
    crawl4ai: Crawl4AIConfig
    lightpanda: Optional[Dict[str, Any]] = None
    library_tracking: Optional[Dict[str, Any]] = None
    benchmarking: Optional[Dict[str, Any]] = None
    logging: Dict[str, Any]

class LibraryOperation(BaseModel):
    """Model for library operations."""
    operation: str
    package_name: str
    status: str = "pending"
    progress: int = 0
    error: Optional[str] = None

    @classmethod
    def validate_package_name(cls, v: str) -> str:
        if not re.match(r'^[a-zA-Z0-9][-a-zA-Z0-9_.]*$', v):
            raise ValueError("Invalid package name format")
        return v

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.scraping_connections: List[WebSocket] = []
        self.library_connections: List[WebSocket] = []
        self.scraping_metrics = {
            "pages_scraped": 0,
            "current_depth": 0,
            "successful_requests": 0,
            "failed_requests": 0,
            "pages_per_second": 0.0,
            "memory_usage": "0 MB",
            "cpu_usage": "0%"
        }
        self.scraping_status = {
            "is_running": False,
            "current_url": None,
            "progress": 0
        }

    async def connect(self, websocket: WebSocket, connection_type: str = "scraping"):
        logging.info(f"New WebSocket connection attempt - Type: {connection_type}")
        await websocket.accept()
        if connection_type == "scraping":
            self.scraping_connections.append(websocket)
            logging.info("Scraping connection established - Sending initial status")
            await websocket.send_json({
                "type": "connection_established",
                "data": self.scraping_status
            })
        elif connection_type == "library":
            self.library_connections.append(websocket)
            logging.info("Library connection established")
            await websocket.send_json({
                "type": "connection_established",
                "data": {"status": "connected"}
            })

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
                await connection.send_json({
                    "type": "metrics",
                    "data": self.scraping_metrics
                })
            except WebSocketDisconnect:
                self.disconnect(connection)

    async def broadcast_scraping_update(self, update: Dict):
        if not self.scraping_connections:
            logging.info("No scraping connections available for broadcast")
            return

        logging.info(f"Broadcasting scraping update to {len(self.scraping_connections)} connections: {update}")
        for connection in self.scraping_connections:
            try:
                await connection.send_json({
                    "type": "scraping_progress",
                    "data": update
                })
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
            "cpu_usage": "0%"
        }

# FastAPI Application Setup
app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize connection manager
manager = ConnectionManager()

# Library management utilities
async def run_uv_command(command: List[str]) -> tuple[int, str, str]:
    """Run a UV package manager command and return its output."""
    logger.info(f"Executing UV command: uv {' '.join(command)}")
    try:
        process = await asyncio.create_subprocess_exec(
            'uv', *command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        return process.returncode, stdout.decode(), stderr.decode()
    except Exception as e:
        logger.error(f"Error executing UV command: {str(e)}", exc_info=True)
        return 1, "", str(e)

async def validate_package_name(name: str) -> bool:
    """Validate a Python package name."""
    pattern = r'^[a-zA-Z0-9][-a-zA-Z0-9_.]*$'
    return bool(re.match(pattern, name))

# Web Routes
@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the home page."""
    return templates.TemplateResponse("scraping_dashboard.html", {"request": request})

@app.get("/api/scraping/backends")
async def get_available_backends():
    """Get available scraping backends."""
    backends = ["crawl4ai", "file"]

    # Check if Lightpanda is available
    try:
        import subprocess
        result = subprocess.run(["lightpanda", "--version"],
                               stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE,
                               text=True,
                               check=False)
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
            "timestamp": data["timestamp"],
            "url": data["url"],
            "status": data["status"],
            "pages_processed": len(data.get("results", []))
        }
        for scraping_id, data in scraping_results_storage.items()
    ]

@app.get("/api/scraping/results/{scraping_id}")
async def get_scraping_results(scraping_id: str):
    """Get scraping results by ID."""
    if scraping_id not in scraping_results_storage:
        raise HTTPException(status_code=404, detail="Scraping results not found")

    return scraping_results_storage[scraping_id]

@app.get("/api/scraping/download/{format}")
async def download_results(format: str):
    """Download scraping results in specified format."""
    if format not in ["json", "markdown", "html"]:
        raise HTTPException(status_code=400, detail="Invalid format specified")

    try:
        if not scraping_results_storage:
            raise HTTPException(status_code=404, detail="No scraping results available")

        latest_id = max(scraping_results_storage.keys())
        results = scraping_results_storage[latest_id]

        if format == "json":
            return JSONResponse(content=results)
        elif format == "markdown":
            markdown_content = "# Documentation Export\n\n"
            for doc in results["results"]:
                markdown_content += f"## {doc.get('content', {}).get('title', 'Untitled')}\n\n"
                markdown_content += f"{doc.get('content', {}).get('text', '')}\n\n"
            return PlainTextResponse(content=markdown_content)
        else:  # html
            html_content = "<html><body>"
            for doc in results["results"]:
                html_content += f"<h2>{doc.get('content', {}).get('title', 'Untitled')}</h2>"
                html_content += f"<div>{doc.get('content', {}).get('text', '')}</div>"
            html_content += "</body></html>"
            return HTMLResponse(content=html_content)

    except Exception as e:
        logging.error(f"Error downloading results: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/libraries", response_class=HTMLResponse)
async def libraries(request: Request):
    """Render the library management page."""
    return templates.TemplateResponse("libraries.html", {"request": request})

@app.websocket("/ws/scraping")
async def scraping_websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket, "scraping")
    try:
        while True:
            data = await websocket.receive_json()
            if data["type"] == "scraping_progress":
                await manager.broadcast_scraping_update(data["data"])
    except WebSocketDisconnect:
        manager.disconnect(websocket)

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
        manager.scraping_status.update({
            "is_running": True,
            "current_url": url,
            "progress": 0
        })

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
                raise HTTPException(status_code=500, detail=f"Failed to initialize Lightpanda backend: {str(e)}")
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
            "results": [result.model_dump() for result in results]
        }

        # Update status
        is_scraping = False
        manager.scraping_status.update({
            "is_running": False,
            "current_url": "",
            "progress": 100
        })

        return {
            "status": "success",
            "scraping_id": scraping_id,
            "results": [result.model_dump() for result in results]
        }
    except Exception as e:
        is_scraping = False
        manager.scraping_status.update({
            "is_running": False,
            "current_url": "",
            "progress": 0
        })
        logging.error(f"Error during crawl: {str(e)}", exc_info=True)
        return {"status": "error", "message": str(e)}

@app.post("/api/scraping/results")
async def store_scraping_results(results: dict):
    """Store scraping results."""
    scraping_id = results.get("scraping_id")
    if not scraping_id:
        scraping_id = f"scrape_{datetime.now().strftime('%Y%m%d%H%M%S')}"
        results["scraping_id"] = scraping_id

    results["timestamp"] = results.get("timestamp", datetime.now().isoformat())

    scraping_results_storage[scraping_id] = results

    return {"status": "success", "scraping_id": scraping_id}

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
        "start_time": datetime.now().isoformat(),
        "end_time": None,
        "output": "",
        "error": ""
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
            library_operations[operation_id].update({
                "status": "completed",
                "end_time": datetime.now().isoformat(),
                "output": f"Documentation for {package_name} has been successfully fetched and processed.",
                "error": ""
            })

        except Exception as e:
            # Handle any exceptions
            library_operations[operation_id].update({
                "status": "failed",
                "end_time": datetime.now().isoformat(),
                "error": str(e)
            })

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
        "start_time": datetime.now().isoformat(),
        "end_time": None,
        "output": "",
        "error": ""
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
            library_operations[operation_id].update({
                "status": "completed",
                "end_time": datetime.now().isoformat(),
                "output": f"Documentation for {package_name} has been successfully removed.",
                "error": ""
            })

        except Exception as e:
            # Handle any exceptions
            library_operations[operation_id].update({
                "status": "failed",
                "end_time": datetime.now().isoformat(),
                "error": str(e)
            })

    # Start background task
    background_tasks.add_task(remove_library_docs_task)

    return {"operation_id": operation_id, "status": "pending"}

@app.get("/api/libraries/operation/{operation_id}")
async def get_library_operation_status(operation_id: str):
    """Get status of a library operation."""
    if operation_id not in library_operations:
        raise HTTPException(status_code=404, detail="Operation not found")

    return library_operations[operation_id]

# CLI Functions
def load_config(config_path: str) -> AppConfig:
    """Load configuration from file."""
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, 'r') as f:
        if config_path.endswith('.json'):
            config_data = json.load(f)
        elif config_path.endswith('.yaml') or config_path.endswith('.yml'):
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
            min_success_rate=0.7
        )
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
                    min_success_rate=0.7
                )
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
        document_organizer=document_organizer
    )

async def run_crawler(
    crawler: DocumentationCrawler,
    targets: list[CrawlTarget]
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
            with open(output_file, 'w') as f:
                json.dump(
                    {
                        "target": target.model_dump(),
                        "stats": result.stats.model_dump(),
                        "documents": result.documents,
                        "issues": [issue.model_dump() for issue in result.issues],
                        "metrics": {
                            k: v.model_dump() for k, v in result.metrics.items()
                        }
                    },
                    f,
                    indent=2,
                    default=str
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
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")

    # Scrape command
    scrape_parser = subparsers.add_parser("scrape", help="Scrape documentation")
    scrape_parser.add_argument(
        '-c', '--config',
        type=str,
        default='config.yaml',
        help='''Path to configuration file (JSON or YAML).
Controls crawler behavior, processing rules, and quality checks.
Default: config.yaml
Environment Variable: LIB2DOCSCRAPE_CONFIG'''
    )

    scrape_parser.add_argument(
        '-t', '--targets',
        type=str,
        required=True,
        help='''Path to targets file (JSON or YAML).
Defines the documentation sites to crawl and their parameters.
Required. Must contain at least one target configuration.'''
    )

    scrape_parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='''Enable verbose logging.
Shows detailed progress and debug information.
Can also be enabled via LIB2DOCSCRAPE_LOG_LEVEL=DEBUG'''
    )

    scrape_parser.add_argument(
        '-d', '--distributed',
        action='store_true',
        help='''Use distributed crawling.
Enables parallel processing of crawl targets using multiple workers.'''
    )

    scrape_parser.add_argument(
        '-w', '--workers',
        type=int,
        default=5,
        help='''Number of workers for distributed crawling (default: 5).
Only used when --distributed is specified.'''
    )

    # Serve command
    serve_parser = subparsers.add_parser("serve", help="Start web server")
    serve_parser.add_argument(
        '-p', '--port',
        type=int,
        default=8000,
        help="Port to run the server on (default: 8000)"
    )

    serve_parser.add_argument(
        '-h', '--host',
        type=str,
        default="127.0.0.1",
        help="Host to bind the server to (default: 127.0.0.1)"
    )

    # Benchmark command
    benchmark_parser = subparsers.add_parser("benchmark", help="Benchmark backends")
    benchmark_parser.add_argument(
        '-u', '--urls',
        type=str,
        required=True,
        help="Comma-separated list of URLs to benchmark"
    )

    benchmark_parser.add_argument(
        '-b', '--backends',
        type=str,
        default="all",
        help="Comma-separated list of backends to benchmark (default: all)"
    )

    benchmark_parser.add_argument(
        '-o', '--output',
        type=str,
        help="Output file for benchmark results"
    )

    benchmark_parser.add_argument(
        '-c', '--config',
        type=str,
        default='config.yaml',
        help="Path to configuration file (JSON or YAML)"
    )

    # Library command
    library_parser = subparsers.add_parser("library", help="Library version management")
    library_subparsers = library_parser.add_subparsers(dest="library_command", help="Library command")

    # Track command
    track_parser = library_subparsers.add_parser("track", help="Track library versions")
    track_parser.add_argument(
        '-n', '--name',
        type=str,
        required=True,
        help="Library name"
    )

    track_parser.add_argument(
        '-v', '--versions',
        type=str,
        required=True,
        help="Comma-separated list of versions to track"
    )

    track_parser.add_argument(
        '-u', '--url',
        type=str,
        help="Base URL for library documentation (optional)"
    )

    # Compare command
    compare_parser = library_subparsers.add_parser("compare", help="Compare library versions")
    compare_parser.add_argument(
        '-n', '--name',
        type=str,
        required=True,
        help="Library name"
    )

    compare_parser.add_argument(
        '-v1', '--version1',
        type=str,
        required=True,
        help="First version"
    )

    compare_parser.add_argument(
        '-v2', '--version2',
        type=str,
        required=True,
        help="Second version"
    )

    compare_parser.add_argument(
        '-o', '--output',
        type=str,
        help="Output file for comparison results"
    )

    # List command
    list_parser = library_subparsers.add_parser("list", help="List tracked libraries")
    list_parser.add_argument(
        '-n', '--name',
        type=str,
        help="Library name (optional)"
    )

    # Visualize command
    visualize_parser = library_subparsers.add_parser("visualize", help="Visualize library version history")
    visualize_parser.add_argument(
        '-n', '--name',
        type=str,
        required=True,
        help="Library name"
    )
    visualize_parser.add_argument(
        '-o', '--output',
        type=str,
        help="Output file for visualization (default: <library_name>_version_history.html)"
    )

    # Categorize command
    categorize_parser = library_subparsers.add_parser("categorize", help="Categorize library documentation")
    categorize_parser.add_argument(
        '-n', '--name',
        type=str,
        required=True,
        help="Library name"
    )
    categorize_parser.add_argument(
        '-v', '--version',
        type=str,
        help="Library version (optional)"
    )
    categorize_parser.add_argument(
        '-c', '--categories',
        type=int,
        default=10,
        help="Number of categories to create (default: 10)"
    )
    categorize_parser.add_argument(
        '-o', '--output',
        type=str,
        help="Output file for categorization model (default: <library_name>_categories.pkl)"
    )

    # Topics command
    topics_parser = library_subparsers.add_parser("topics", help="Extract topics from library documentation")
    topics_parser.add_argument(
        '-n', '--name',
        type=str,
        required=True,
        help="Library name"
    )
    topics_parser.add_argument(
        '-v', '--version',
        type=str,
        help="Library version (optional)"
    )
    topics_parser.add_argument(
        '-t', '--topics',
        type=int,
        default=10,
        help="Number of topics to extract (default: 10)"
    )
    topics_parser.add_argument(
        '-o', '--output',
        type=str,
        help="Output file for topic model (default: <library_name>_topics.pkl)"
    )

    # Package command
    package_parser = library_subparsers.add_parser("package", help="Manage Python packages")
    package_parser.add_argument(
        'package_action',
        choices=['install', 'uninstall', 'list'],
        help="Package action to perform"
    )
    package_parser.add_argument(
        'package_name',
        type=str,
        nargs='?',
        help="Package name"
    )
    package_parser.add_argument(
        '-v', '--version',
        type=str,
        help="Package version (for install)"
    )
    package_parser.add_argument(
        '--use-uv',
        action='store_true',
        default=True,
        help="Use uv package manager (default: True)"
    )
    package_parser.add_argument(
        '--use-pip',
        action='store_true',
        help="Use pip package manager instead of uv"
    )

    # Common arguments for all commands
    parser.add_argument(
        '--verbose',
        action='store_true',
        help="Enable verbose logging"
    )

    return parser.parse_args()

def load_targets(targets_path: str) -> list[CrawlTarget]:
    """Load crawl targets from file."""
    if not os.path.exists(targets_path):
        raise FileNotFoundError(f"Targets file not found: {targets_path}")

    with open(targets_path, 'r') as f:
        if targets_path.endswith('.json'):
            targets_data = json.load(f)
        elif targets_path.endswith('.yaml') or targets_path.endswith('.yml'):
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
    urls = [url.strip() for url in args.urls.split(',')]

    # Parse backends
    backends = args.backends.split(',') if args.backends != "all" else "all"

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
                from .backends.crawl4ai import Crawl4AIBackend, Crawl4AIConfig
                crawl4ai_backend = Crawl4AIBackend(config=Crawl4AIConfig())
                benchmark.register_backend(crawl4ai_backend)
            elif backend_name == "lightpanda":
                from .backends.lightpanda_backend import LightpandaBackend, LightpandaConfig
                lightpanda_backend = LightpandaBackend(config=LightpandaConfig())
                benchmark.register_backend(lightpanda_backend)
            elif backend_name == "file":
                from .backends.file_backend import FileBackend
                file_backend = FileBackend()
                benchmark.register_backend(file_backend)

    # Run benchmark
    logging.info(f"Running benchmark on {len(urls)} URLs with {len(benchmark.backends)} backends")
    for url in urls:
        logging.info(f"Benchmarking URL: {url}")
        results = await benchmark.benchmark_url(url)

        # Log results
        for backend_name, result in results.items():
            if result.success:
                logging.info(f"  {backend_name}: Success, {result.crawl_time:.2f}s, {result.content_size} bytes")
            else:
                logging.info(f"  {backend_name}: Failed, {result.error}")

    # Generate report
    output_file = args.output or f"benchmark_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
    benchmark.generate_report(output_file)
    logging.info(f"Benchmark report saved to {output_file}")

    # Close backends
    await benchmark.close()

async def run_library_track(args) -> None:
    """Run library track command."""
    # Parse versions
    versions = [v.strip() for v in args.versions.split(',')]

    # Create library registry and version tracker
    registry = LibraryRegistry()
    tracker = LibraryVersionTracker(registry)

    # Add library to registry if URL is provided
    if args.url:
        registry.add_library(args.name, args.url)

    # Create doc site verifier
    verifier = DocSiteVerifier()

    # Track each version
    for version in versions:
        # Get documentation URL
        doc_url = registry.get_doc_url(args.name, version)
        if not doc_url:
            # Try to get URL from verifier
            pattern = verifier.get_library_from_name(args.name)
            if pattern:
                doc_url = verifier.get_doc_url_from_name(args.name, version)

            if not doc_url:
                logging.error(f"Could not determine documentation URL for {args.name} {version}")
                continue

        logging.info(f"Tracking {args.name} {version} at {doc_url}")

        # Create a crawler to fetch the documentation
        # In a real implementation, this would use the crawler to fetch and process the documentation
        # For now, we'll just create a dummy ProcessedContent
        from src.processors.content.models import ProcessedContent
        content = ProcessedContent()
        content.url = doc_url
        content.title = f"{args.name} {version} Documentation"

        # Add to tracker
        doc_id = tracker.add_documentation(args.name, version, content)
        logging.info(f"Added documentation for {args.name} {version} with ID {doc_id}")

    # Save registry
    registry_file = f"{args.name}_registry.json"
    registry.save_to_file(registry_file)
    logging.info(f"Library registry saved to {registry_file}")

async def run_library_compare(args) -> None:
    """Run library compare command."""
    # Load registry
    registry_file = f"{args.name}_registry.json"
    try:
        registry = LibraryRegistry.load_from_file(registry_file)
    except Exception as e:
        logging.error(f"Error loading registry: {e}")
        registry = LibraryRegistry()

    # Create version tracker
    tracker = LibraryVersionTracker(registry)

    # Compare versions
    diff = tracker.compare_versions(args.name, args.version1, args.version2)

    # Generate report
    output_file = args.output or f"{args.name}_diff_{args.version1}_vs_{args.version2}.md"
    with open(output_file, 'w') as f:
        f.write(f"# {args.name} Documentation Diff: {args.version1} vs {args.version2}\n\n")

        f.write("## Summary\n\n")
        f.write(f"* Added pages: {len(diff.added_pages)}\n")
        f.write(f"* Removed pages: {len(diff.removed_pages)}\n")
        f.write(f"* Modified pages: {len(diff.modified_pages)}\n\n")

        if diff.added_pages:
            f.write("## Added Pages\n\n")
            for url in diff.added_pages:
                f.write(f"* {url}\n")
            f.write("\n")

        if diff.removed_pages:
            f.write("## Removed Pages\n\n")
            for url in diff.removed_pages:
                f.write(f"* {url}\n")
            f.write("\n")

        if diff.modified_pages:
            f.write("## Modified Pages\n\n")
            for url in diff.modified_pages:
                f.write(f"* {url}\n")
            f.write("\n")

        if diff.diff_details:
            f.write("## Detailed Diffs\n\n")
            for url, details in diff.diff_details.items():
                f.write(f"### {url}\n\n")
                f.write(f"**Title in {args.version1}**: {details.get('title1', 'N/A')}\n\n")
                f.write(f"**Title in {args.version2}**: {details.get('title2', 'N/A')}\n\n")
                f.write("```diff\n")
                for line in details.get('diff', []):
                    f.write(f"{line}\n")
                f.write("```\n\n")

    logging.info(f"Comparison report saved to {output_file}")

async def run_library_list(args) -> None:
    """Run library list command."""
    # Load registry
    if args.name:
        registry_file = f"{args.name}_registry.json"
    else:
        registry_file = "library_registry.json"

    try:
        registry = LibraryRegistry.load_from_file(registry_file)
    except Exception as e:
        logging.error(f"Error loading registry: {e}")
        registry = LibraryRegistry()

    # List libraries
    if args.name:
        # List specific library
        library = registry.get_library(args.name)
        if not library:
            logging.error(f"Library {args.name} not found in registry")
            return

        logging.info(f"Library: {args.name}")
        logging.info(f"Base URL: {library.get('base_url', 'N/A')}")
        logging.info(f"Versions: {', '.join(library.get('versions', {}).keys())}")
    else:
        # List all libraries
        logging.info(f"Registered libraries: {len(registry.libraries)}")
        for name, library in registry.libraries.items():
            logging.info(f"  {name}: {len(library.get('versions', {}))} versions")

async def run_library_visualize(args) -> None:
    """Run library visualization command."""
    # Load registry
    registry_file = f"{args.name}_registry.json"
    try:
        registry = LibraryRegistry.load_from_file(registry_file)
    except Exception as e:
        logging.error(f"Error loading registry: {e}")
        registry = LibraryRegistry()

    # Create version tracker and visualizer
    tracker = LibraryVersionTracker(registry)
    visualizer = VersionHistoryVisualizer(tracker=tracker)

    try:
        # Create version graph
        graph = visualizer.create_version_graph(args.name)

        # Generate visualization
        output_file = args.output or f"{args.name}_version_history.html"
        visualizer.generate_html_visualization(graph, output_file)

        logging.info(f"Version history visualization saved to {output_file}")

        # Open in browser if available
        try:
            import webbrowser
            webbrowser.open(f"file://{os.path.abspath(output_file)}")
        except Exception as e:
            logging.warning(f"Could not open browser: {e}")
    except Exception as e:
        logging.error(f"Error generating visualization: {e}")

async def run_library_categorize(args) -> None:
    """Run library categorization command."""
    # Load registry
    registry_file = f"{args.name}_registry.json"
    try:
        registry = LibraryRegistry.load_from_file(registry_file)
    except Exception as e:
        logging.error(f"Error loading registry: {e}")
        registry = LibraryRegistry()

    # Create version tracker
    tracker = LibraryVersionTracker(registry)

    # Get library
    library = registry.get_library(args.name)
    if not library:
        logging.error(f"Library {args.name} not found in registry")
        return

    # Get versions
    if args.version:
        versions = [args.version]
    else:
        versions = list(library.get("versions", {}).keys())

    if not versions:
        logging.error(f"No versions found for library {args.name}")
        return

    # Get documents
    documents = []
    for version in versions:
        version_data = library["versions"].get(version)
        if not version_data:
            logging.warning(f"Version {version} not found for library {args.name}")
            continue

        version_docs = version_data.get("documents", [])
        if not version_docs:
            logging.warning(f"No documents found for {args.name} {version}")
            continue

        documents.extend(version_docs)

    if not documents:
        logging.error(f"No documents found for library {args.name}")
        return

    # Create categorizer
    categorizer = DocumentCategorizer()

    # Train model
    logging.info(f"Training categorization model with {len(documents)} documents and {args.categories} categories")
    categorizer.train_model(documents, num_categories=args.categories)

    # Save model
    output_file = args.output or f"{args.name}_categories.pkl"
    categorizer.save_model(output_file)

    logging.info(f"Categorization model saved to {output_file}")

    # Print categories
    logging.info("Categories:")
    for cat_id, category in categorizer.model.categories.items():
        logging.info(f"  {category.name}: {', '.join(category.keywords)}")

async def run_library_topics(args) -> None:
    """Run library topic modeling command."""
    # Load registry
    registry_file = f"{args.name}_registry.json"
    try:
        registry = LibraryRegistry.load_from_file(registry_file)
    except Exception as e:
        logging.error(f"Error loading registry: {e}")
        registry = LibraryRegistry()

    # Create version tracker
    tracker = LibraryVersionTracker(registry)

    # Get library
    library = registry.get_library(args.name)
    if not library:
        logging.error(f"Library {args.name} not found in registry")
        return

    # Get versions
    if args.version:
        versions = [args.version]
    else:
        versions = list(library.get("versions", {}).keys())

    if not versions:
        logging.error(f"No versions found for library {args.name}")
        return

    # Get documents
    documents = []
    for version in versions:
        version_data = library["versions"].get(version)
        if not version_data:
            logging.warning(f"Version {version} not found for library {args.name}")
            continue

        version_docs = version_data.get("documents", [])
        if not version_docs:
            logging.warning(f"No documents found for {args.name} {version}")
            continue

        documents.extend(version_docs)

    if not documents:
        logging.error(f"No documents found for library {args.name}")
        return

    # Create topic modeler
    topic_modeler = TopicModeler()

    # Train model
    logging.info(f"Training topic model with {len(documents)} documents and {args.topics} topics")
    topic_modeler.train_model(documents, num_topics=args.topics)

    # Save model
    output_file = args.output or f"{args.name}_topics.pkl"
    topic_modeler.save_model(output_file)

    logging.info(f"Topic model saved to {output_file}")

    # Print topics
    logging.info("Topics:")
    for topic_id, topic in topic_modeler.model.topics.items():
        logging.info(f"  {topic.name} ({topic.weight:.2f}): {', '.join(topic.keywords)}")

async def run_package_command(args) -> None:
    """Run package management command."""
    # Create package manager
    config = PackageManagerConfig(
        use_uv=args.use_uv and not args.use_pip
    )
    package_manager = PackageManager(config=config)

    if args.package_action == "install":
        if not args.package_name:
            logging.error("Package name is required for install action")
            return

        logging.info(f"Installing package {args.package_name}{f' version {args.version}' if args.version else ''}")
        success, output = await package_manager.install_package(args.package_name, args.version)

        if success:
            logging.info(f"Successfully installed {args.package_name}")
            logging.info(output)
        else:
            logging.error(f"Failed to install {args.package_name}")
            logging.error(output)

    elif args.package_action == "uninstall":
        if not args.package_name:
            logging.error("Package name is required for uninstall action")
            return

        logging.info(f"Uninstalling package {args.package_name}")
        success, output = await package_manager.uninstall_package(args.package_name)

        if success:
            logging.info(f"Successfully uninstalled {args.package_name}")
            logging.info(output)
        else:
            logging.error(f"Failed to uninstall {args.package_name}")
            logging.error(output)

    elif args.package_action == "list":
        # Use pip list or uv pip list to show installed packages
        cmd = [package_manager.uv_path, "pip", "list"] if package_manager.uv_path and args.use_uv else [package_manager.pip_path, "list"]

        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()

            if process.returncode == 0:
                logging.info("Installed packages:")
                print(stdout.decode())
            else:
                logging.error(f"Failed to list packages: {stderr.decode()}")
        except Exception as e:
            logging.error(f"Error listing packages: {str(e)}")

def main() -> None:
    """Main entry point."""
    args = parse_args()

    try:
        # Setup logging
        log_level = "DEBUG" if getattr(args, 'verbose', False) else "INFO"
        setup_logging(level=log_level)

        # Handle commands
        if args.command == "scrape":
            # Load configuration
            config = load_config(args.config)

            # Load targets
            targets = load_targets(args.targets)

            if args.distributed:
                # Run with distributed crawling
                logging.info(f"Running with distributed crawling ({args.workers} workers)")

                # Create distributed config
                dist_config = DistributedConfig(
                    max_workers=args.workers,
                    task_timeout=300,
                    retry_count=3,
                    heartbeat_interval=10,
                    metrics_enabled=args.verbose
                )

                # Create runner
                runner = DistributedCrawlRunner(config=dist_config)

                # Run distributed crawling
                asyncio.run(runner.run(targets, args.workers))
            else:
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

        elif args.command == "library":
            # Handle library commands
            if args.library_command == "track":
                asyncio.run(run_library_track(args))
            elif args.library_command == "compare":
                asyncio.run(run_library_compare(args))
            elif args.library_command == "list":
                asyncio.run(run_library_list(args))
            elif args.library_command == "visualize":
                asyncio.run(run_library_visualize(args))
            elif args.library_command == "categorize":
                asyncio.run(run_library_categorize(args))
            elif args.library_command == "topics":
                asyncio.run(run_library_topics(args))
            elif args.library_command == "package":
                asyncio.run(run_package_command(args))
            else:
                logging.error(f"Unknown library command: {args.library_command}")

        else:
            logging.error(f"Unknown command: {args.command}")

    except Exception as e:
        logging.error(f"Error: {str(e)}")
        raise

if __name__ == "__main__":
    main()