#!/usr/bin/env python3
"""Run the Crawl4AI testing interface."""

import asyncio
import base64
import logging
import os
import re
import socket
import ssl
import sys
import tempfile
import webbrowser
import zipfile
from contextlib import closing
from threading import Timer
from typing import Any, Optional
from urllib.parse import urljoin, urlparse

import aiohttp
import html2text
import uvicorn
from bs4 import BeautifulSoup
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.templating import Jinja2Templates
from starlette.responses import HTMLResponse, JSONResponse, Response
from starlette.staticfiles import StaticFiles
from starlette.websockets import WebSocketState

from src.backends.crawl4ai_backend import Crawl4AIBackend, Crawl4AIConfig
from src.backends.crawl4ai_backend import Crawl4AIBackend as Crawler
from src.backends.crawl4ai_backend import Crawl4AIConfig as Config
from src.backends.selector import BackendSelector
from src.utils.search import DuckDuckGoSearch
from src.utils.url.factory import create_url_info

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("crawler.log")],
)
logger = logging.getLogger(__name__)

# Global variables for storing crawl results and active tasks
crawl_results = {}
active_scraping_tasks = {}
active_websockets = set()
socket_lock = asyncio.Lock()


async def search_duckduckgo(query: str) -> list[dict]:
    """Search DuckDuckGo for documentation URLs."""
    try:
        ddg_search = DuckDuckGoSearch(max_results=10)
        results = await ddg_search.search(query)

        # Transform results to match expected format
        formatted_results = []
        for result in results:
            formatted_results.append(
                {"url": result.get("url", ""), "source": "DuckDuckGo Search"}
            )

        return formatted_results
    except Exception as e:
        logger.error(f"DuckDuckGo search error: {str(e)}")
        return []


def find_free_port():
    """Find a free port to use for the server."""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(("", 0))
        s.listen(1)
        port = s.getsockname()[1]
        return port


class DomainConfig:
    """Configuration for specific documentation domains."""

    def __init__(
        self, domain: str, patterns: list[str] = None, selectors: list[str] = None
    ):
        self.domain = domain
        self.content_patterns = patterns or []  # URL patterns to match
        self.content_selectors = selectors or []  # CSS selectors for main content


# Common documentation site configurations
DOMAIN_CONFIGS = {
    "promptfoo.dev": DomainConfig(
        domain="promptfoo.dev",
        patterns=[r"/docs/intro$", r"/docs/.*"],
        selectors=[".theme-doc-markdown", ".markdown"],
    ),
    "firecrawl.dev": DomainConfig(
        domain="firecrawl.dev",
        patterns=[r"/docs/intro$", r"/docs/.*"],
        selectors=[".theme-doc-markdown", ".markdown"],
    ),
    "docs.python.org": DomainConfig(
        domain="docs.python.org", patterns=[r"/3/.*"], selectors=[".body", ".document"]
    ),
    "docs.pytest.org": DomainConfig(
        domain="docs.pytest.org", patterns=[r"/en/.*"], selectors=[".document", ".body"]
    ),
    "fastapi.tiangolo.com": DomainConfig(
        domain="fastapi.tiangolo.com",
        patterns=[r"/.*"],
        selectors=[".md-content__inner", ".markdown-body"],
    ),
    "react.dev": DomainConfig(
        domain="react.dev",
        patterns=[r"/learn.*", r"/reference.*", r"/blog.*"],
        selectors=[".markdown", ".article-content"],
    ),
    "docs.github.com": DomainConfig(
        domain="docs.github.com",
        patterns=[r"/.*"],
        selectors=[".markdown-body", ".article-body"],
    ),
}


def get_domain_config(url: str) -> Optional[DomainConfig]:
    """Get domain-specific configuration for a URL."""
    try:
        domain = urlparse(url).netloc
        return DOMAIN_CONFIGS.get(domain)
    except Exception:
        return None


def normalize_url(url: str) -> str:
    """Normalize URLs with domain-specific handling."""
    # Create URLInfo using the factory
    url_info = create_url_info(url)

    # If URL is invalid, return original
    if not url_info.is_valid:
        logger.error(f"Invalid URL {url}: {url_info.error_message}")
        return url

    # Apply domain-specific handling
    try:
        parsed = urlparse(url_info.normalized_url)
        domain = parsed.netloc
        path = parsed.path.rstrip("/")

        # Get domain-specific config
        config = DOMAIN_CONFIGS.get(domain)
        if config:
            # Check if URL matches any domain-specific patterns
            for pattern in config.content_patterns:
                if re.search(pattern + "$", path):
                    return url_info.normalized_url

            # Apply domain-specific normalization
            if domain == "promptfoo.dev" and path == "/docs":
                return "https://promptfoo.dev/docs/intro"
            elif domain == "firecrawl.dev" and path == "/docs":
                return "https://firecrawl.dev/docs/intro"
            elif domain == "docs.python.org" and path == "/3":
                return "https://docs.python.org/3/tutorial/index.html"
            elif domain == "react.dev" and path == "":
                return "https://react.dev/learn"
    except Exception as e:
        logger.error(f"Error in domain-specific normalization for URL {url}: {str(e)}")

    return url_info.normalized_url


def clean_and_convert_html(html: str, url: str) -> str:
    """Clean HTML with domain-specific handling."""
    soup = BeautifulSoup(html, "html.parser")

    # Get domain-specific config
    config = get_domain_config(url)
    main_content = None

    if config:
        # Try domain-specific content selectors first
        for selector in config.content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break

    # If no domain-specific content found, try generic selectors
    if not main_content:
        content_selectors = [
            "main",
            "article",
            '[role="main"]',
            ".main-content",
            ".content",
            ".document",
            ".markdown-body",
            ".md-content",
            "#content",
            ".post-content",
            ".entry-content",
            ".theme-doc-markdown",
            ".prose",
            ".docusaurus-highlight-code-line",
            ".docs-markdown",
            ".documentation-content",
            ".sphinx-content",
            ".rst-content",
            ".section",
            ".body",
            ".page-content",
            ".main-container",
            ".doc-content",
        ]

        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break

    if not main_content:
        main_content = soup.body or soup

    # Remove unwanted elements
    for element in main_content.select(
        "script, style, iframe, nav, footer, header, .sidebar, .navigation-menu"
    ):
        element.decompose()

    # Convert to markdown while preserving structure
    h = html2text.HTML2Text()
    h.body_width = 0  # Don't wrap lines
    h.ignore_links = False
    h.ignore_images = False
    h.ignore_emphasis = False
    h.ignore_tables = False
    h.mark_code = True

    return h.handle(str(main_content))


async def fetch_url(
    url: str,
    session: aiohttp.ClientSession,
    max_retries: int = 3,
    base_delay: float = 1.0,
) -> tuple[str, int]:
    """Fetch URL content with improved error handling and retry logic."""
    url = normalize_url(url)
    delay = base_delay

    logger.info(f"Normalized URL: {url}")

    for attempt in range(max_retries):
        try:
            logger.debug(f"Attempt {attempt + 1}/{max_retries}")
            async with session.get(
                url, ssl=False if url.startswith("https://localhost") else True
            ) as response:
                if response.status == 404:
                    # Try common alternatives
                    alternatives = [
                        "https://promptfoo.dev/docs/intro",  # Direct try for promptfoo
                        url + "/intro",
                        url.rstrip("/") + "/introduction",
                        url.rstrip("/") + "/getting-started",
                        re.sub(r"/docs/?$", "/docs/intro", url),
                        re.sub(r"/docs/?$", "/docs/getting-started", url),
                    ]

                    for alt_url in alternatives:
                        logger.info(f"Trying alternative URL: {alt_url}")
                        try:
                            async with session.get(
                                alt_url,
                                ssl=False
                                if alt_url.startswith("https://localhost")
                                else True,
                            ) as alt_response:
                                if alt_response.status == 200:
                                    return (
                                        await alt_response.text(),
                                        alt_response.status,
                                    )
                        except Exception as e:
                            logger.debug(
                                f"Failed to fetch alternative URL {alt_url}: {str(e)}"
                            )
                            continue

                return await response.text(), response.status

        except (aiohttp.ClientError, asyncio.TimeoutError):
            if attempt < max_retries - 1:
                logger.debug(f"Waiting {delay}s before retry")
                await asyncio.sleep(delay)
                delay *= 2  # Exponential backoff
            else:
                logger.error(f"All retry attempts failed for {url}")
                raise

    return "", 500


class DocFinder:
    def __init__(self):
        self.known_doc_patterns = {
            "readthedocs.io": lambda pkg: f"https://{pkg}.readthedocs.io/",
            "readthedocs.org": lambda pkg: f"https://{pkg}.readthedocs.org/",
            "github.io": lambda pkg: f"https://{pkg}.github.io/",
        }

        self.package_registries = {
            "pypi": "https://pypi.org/pypi/{package}/json",
            "npm": "https://registry.npmjs.org/{package}",
        }

    async def find_github_docs(self, repo_path: str) -> list[dict[str, str]]:
        """Find documentation for a GitHub repository."""
        try:
            # Clean the repo path
            repo_path = (
                repo_path.replace("github.com/", "")
                .replace("https://", "")
                .replace("http://", "")
            )
            api_url = f"https://api.github.com/repos/{repo_path}"

            headers = {}
            if os.environ.get("GITHUB_TOKEN"):
                headers["Authorization"] = f"token {os.environ['GITHUB_TOKEN']}"

            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            connector = aiohttp.TCPConnector(ssl=ssl_context)

            async with aiohttp.ClientSession(connector=connector) as session:
                async with session.get(api_url, headers=headers) as response:
                    if response.status != 200:
                        return []

                    repo_data = await response.json()
                    docs_urls = []

                    # Check for GitHub Pages
                    if repo_data.get("has_pages"):
                        docs_urls.append(
                            {
                                "url": f"https://{repo_data['owner']['login']}.github.io/{repo_data['name']}/",
                                "source": "GitHub Pages",
                            }
                        )

                    # Check common doc locations
                    doc_paths = ["docs/", "doc/", "documentation/", "wiki/"]
                    for path in doc_paths:
                        check_url = f"https://github.com/{repo_path}/tree/main/{path}"
                        async with session.get(check_url) as doc_response:
                            if doc_response.status == 200:
                                docs_urls.append(
                                    {"url": check_url, "source": f"GitHub {path}"}
                                )

                    return docs_urls
        except Exception as e:
            logger.error(f"Error finding GitHub docs: {str(e)}")
            return []


async def get_package_docs(package_name: str) -> dict[str, Any]:
    """Get documentation URLs and info for a package."""
    try:
        # Try PyPI first
        pypi_url = f"https://pypi.org/pypi/{package_name}/json"
        logger.info(f"Fetching PyPI info for {package_name}")

        docs = []
        async with aiohttp.ClientSession() as session:
            async with session.get(pypi_url) as response:
                if response.status == 200:
                    data = await response.json()
                    info = data["info"]

                    # Project URLs
                    if "project_urls" in info and info["project_urls"]:
                        for label, url in info["project_urls"].items():
                            if url and any(
                                keyword in label.lower()
                                for keyword in ["doc", "wiki", "guide", "manual"]
                            ):
                                docs.append({"url": url, "source": f"PyPI {label}"})

                    # Documentation URL
                    if info.get("docs_url"):
                        docs.append(
                            {"url": info["docs_url"], "source": "PyPI Documentation"}
                        )

                    # Project Homepage
                    if info.get("home_page"):
                        docs.append(
                            {"url": info["home_page"], "source": "Project Homepage"}
                        )

                    # ReadTheDocs
                    rtd_url = f"https://{package_name}.readthedocs.io/"
                    try:
                        async with session.get(rtd_url) as rtd_response:
                            if rtd_response.status == 200:
                                docs.append({"url": rtd_url, "source": "ReadTheDocs"})
                    except Exception:
                        pass

                    # DuckDuckGo Search
                    ddg_results = await search_duckduckgo(
                        f"{package_name} python documentation"
                    )
                    docs.extend(ddg_results)

                    # Remove duplicates while preserving order
                    seen_urls = set()
                    unique_docs = []
                    for doc in docs:
                        if doc["url"] not in seen_urls:
                            seen_urls.add(doc["url"])
                            unique_docs.append(doc)
                    docs = unique_docs

                    if docs:
                        return {
                            "name": package_name,
                            "version": info.get("version", "unknown"),
                            "summary": info.get("summary", ""),
                            "docs": docs,
                        }

                    logger.warning(f"No documentation found for {package_name}")
                    return {"name": package_name, "error": "No documentation found"}

                # If PyPI fails, try DuckDuckGo
                docs = await search_duckduckgo(f"{package_name} documentation")
                if docs:
                    return {"name": package_name, "docs": docs}

                logger.error(f"Package {package_name} not found on PyPI")
                return {"name": package_name, "error": "Package not found on PyPI"}

    except Exception as e:
        logger.error(f"Error fetching docs for {package_name}: {str(e)}")
        return {"name": package_name, "error": str(e)}


app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For development only
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Global variables for WebSocket management
active_websockets: set[WebSocket] = set()
socket_lock = asyncio.Lock()
scraping_results = {}
active_scraping_websockets: set[WebSocket] = set()
scraping_results = {}


@app.websocket("/ws/scraping")
async def scraping_websocket(websocket: WebSocket):
    """Handle WebSocket connections for scraping updates."""
    try:
        await websocket.accept()
        logger.info("Scraping WebSocket connection accepted")

        async with socket_lock:
            active_scraping_websockets.add(websocket)

        try:
            while True:
                data = await websocket.receive_json()
                logger.info(f"Received scraping WebSocket message: {data}")

                if data.get("type") == "start_scraping":
                    urls = data.get("urls", [])
                    if not urls:
                        await websocket.send_json(
                            {"type": "error", "message": "No URLs provided"}
                        )
                    else:
                        await handle_scraping(websocket, urls)
                else:
                    await websocket.send_json(
                        {"type": "error", "message": "Unknown message type"}
                    )

        except WebSocketDisconnect:
            logger.info("Scraping WebSocket disconnected")
            raise

    except Exception as e:
        logger.error(f"Error in scraping websocket: {str(e)}")
        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.send_json({"type": "error", "message": str(e)})

    finally:
        async with socket_lock:
            if websocket in active_scraping_websockets:
                active_scraping_websockets.remove(websocket)
        logger.info("Scraping WebSocket connection cleaned up")


@app.get("/api/libraries")
async def get_libraries():
    """Get list of available libraries."""
    logger.info("Getting libraries list")
    try:
        # TODO: Implement actual library fetching
        libraries = []
        return JSONResponse({"status": "success", "libraries": libraries})
    except Exception as e:
        logger.error(f"Error getting libraries: {str(e)}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


@app.get("/api/test-config")
async def get_test_config():
    """Get test configuration."""
    logger.info("Getting test configuration")
    try:
        # TODO: Implement actual config fetching
        config = {"max_pages": 10, "follow_links": True, "concurrent_requests": 5}
        return JSONResponse({"status": "success", "config": config})
    except Exception as e:
        logger.error(f"Error getting test config: {str(e)}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


@app.get("/api/test-results")
async def get_test_results():
    """Get test results."""
    logger.info("Getting test results")
    try:
        results = list(scraping_results.items())
        return JSONResponse({"status": "success", "results": results})
    except Exception as e:
        logger.error(f"Error getting test results: {str(e)}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


@app.post("/api/scraping/start")
async def start_scraping(request: Request):
    """Start the scraping process."""
    try:
        data = await request.json()
        logger.info(f"Received scraping request with data: {data}")

        # Extract URLs from request data
        urls = []
        if isinstance(data, dict):
            # Handle 'urls' field
            if "urls" in data:
                if isinstance(data["urls"], list):
                    urls = data["urls"]
                elif isinstance(data["urls"], str):
                    urls = [data["urls"]]
            # Handle 'url' field
            elif "url" in data:
                urls = [data["url"]]
        elif isinstance(data, list):
            urls = data
        elif isinstance(data, str):
            urls = [data]

        # Validate we have URLs to process
        if not urls:
            logger.warning("No URLs provided in request")
            return JSONResponse(
                {"status": "error", "message": "No URLs provided"}, status_code=400
            )

        # Validate URLs
        valid_urls = []
        for url in urls:
            url_info = create_url_info(url)
            if url_info.is_valid:
                valid_urls.append(url_info.normalized_url)
            else:
                logger.warning(f"Invalid URL skipped: {url} - {url_info.error_message}")

        if not valid_urls:
            return JSONResponse(
                {"status": "error", "message": "No valid URLs provided"},
                status_code=400,
            )

        # Create and track the scraping task
        task_id = str(hash(tuple(valid_urls)))
        task = asyncio.create_task(handle_scraping_background(valid_urls))
        active_scraping_tasks[task_id] = task

        return JSONResponse(
            {
                "status": "success",
                "message": f"Scraping started for {len(valid_urls)} URLs",
                "urls": valid_urls,
                "task_id": task_id,
            }
        )

    except ValueError as ve:
        logger.error(f"Validation error in start_scraping: {str(ve)}")
        return JSONResponse({"status": "error", "message": str(ve)}, status_code=400)
    except Exception as e:
        logger.error(f"Error in start_scraping: {str(e)}")
        return JSONResponse(
            {"status": "error", "message": f"Internal server error: {str(e)}"},
            status_code=500,
        )


# Global variable to track active scraping tasks
active_scraping_tasks: dict[str, asyncio.Task] = {}


@app.post("/api/scraping/stop")
async def stop_scraping(request: Request):
    """Stop any ongoing scraping processes."""
    try:
        data = await request.json()
        task_id = data.get("task_id")

        if task_id and task_id in active_scraping_tasks:
            # Cancel the specific task
            task = active_scraping_tasks[task_id]
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            del active_scraping_tasks[task_id]
            return JSONResponse(
                {"status": "success", "message": f"Scraping task {task_id} stopped"}
            )
        elif not task_id:
            # Stop all tasks
            tasks_stopped = 0
            for _task_id, task in active_scraping_tasks.items():
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                    tasks_stopped += 1
            active_scraping_tasks.clear()
            return JSONResponse(
                {
                    "status": "success",
                    "message": f"Stopped {tasks_stopped} scraping tasks",
                }
            )
        else:
            return JSONResponse(
                {"status": "error", "message": f"Task {task_id} not found"},
                status_code=404,
            )

    except Exception as e:
        logger.error(f"Error in stop_scraping: {str(e)}")
        return JSONResponse(
            {"status": "error", "message": f"Internal server error: {str(e)}"},
            status_code=500,
        )


async def handle_scraping_background(
    urls: list[str], websocket: Optional[WebSocket] = None
):
    """Handle scraping in background."""
    config = Config(max_pages=10, follow_links=True, concurrent_requests=5)
    crawler = Crawler(config)

    for url in urls:
        try:
            logger.info(f"Starting scraping for URL: {url}")
            result = await crawler.crawl(url)
            if result.error:
                logger.error(f"Error scraping {url}: {result.error}")
            else:
                scraping_results[url] = result.content
        except Exception as e:
            logger.error(f"Error scraping URL {url}: {str(e)}")


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the main scraping dashboard."""
    return templates.TemplateResponse(
        request, "scraping_dashboard.html", {"request": request}
    )


@app.get("/home", response_class=HTMLResponse)
async def home_page(request: Request):
    """Render the welcome/info page."""
    return templates.TemplateResponse(request, "index.html", {"request": request})


@app.get("/test-dashboard", response_class=HTMLResponse)
async def test_dashboard(request: Request):
    """Render the test dashboard page."""
    return templates.TemplateResponse(
        request, "scraping_dashboard.html", {"request": request}
    )


@app.get("/libraries", response_class=HTMLResponse)
async def libraries(request: Request):
    """Render the libraries page."""
    return templates.TemplateResponse(request, "libraries.html", {"request": request})


@app.get("/config", response_class=HTMLResponse)
async def config(request: Request):
    """Render the configuration page."""
    return templates.TemplateResponse(request, "config.html", {"request": request})


@app.get("/results", response_class=HTMLResponse)
async def results(request: Request):
    """Render the results page."""
    return templates.TemplateResponse(request, "results.html", {"request": request})


@app.post("/crawl")
async def crawl(request: Request):
    try:
        data = await request.json()
        url = data.get("url", "")
        max_pages = data.get("max_pages", 10)

        if not url:
            return {"error": "URL is required"}

        # Create a new crawler instance
        config = Config(max_pages=max_pages, follow_links=True, concurrent_requests=5)
        crawler = Crawler(config)

        # Create progress callback
        async def progress_callback(url: str, depth: int, status: str):
            try:
                if status == "success":
                    async with aiohttp.ClientSession() as session:
                        try:
                            html, status_code = await fetch_url(url, session)
                            if status_code == 200:
                                # Convert HTML to Markdown
                                markdown_content = clean_and_convert_html(html, url)
                                crawl_results[url] = markdown_content
                        except Exception as e:
                            logger.error(f"Error fetching URL {url}: {str(e)}")
                        finally:
                            await session.close()
            except Exception as e:
                logger.error(f"Error in progress callback: {str(e)}")

        # Set up progress callback
        crawler._progress_callback = progress_callback

        # Start crawling
        await crawler.crawl(url)

        return {"message": "Crawl started"}

    except Exception as e:
        logger.error(f"Error in /crawl endpoint: {str(e)}")
        return {"error": str(e)}


@app.get("/content/{b64url}")
async def get_content(b64url: str):
    try:
        # Decode the base64 URL
        url = base64.b64decode(b64url.encode()).decode()
        # Return the stored content
        content = crawl_results.get(url, "")
        if not content:
            return JSONResponse({"error": "Content not found"}, status_code=404)

        # Return as plain text for markdown
        return Response(content=content, media_type="text/plain")
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=400)


@app.post("/export")
async def export_docs(request: Request):
    try:
        data = await request.json()
        base_url = data.get("baseUrl", "")
        results = data.get("results", {})

        if not base_url or not results:
            return JSONResponse({"error": "Missing data"}, status_code=400)

        # Create a temporary directory for the documentation
        with tempfile.TemporaryDirectory() as temp_dir:
            # Get domain name for the folder
            domain = urlparse(base_url).netloc
            docs_dir = os.path.join(temp_dir, f"{domain}_Documentation")
            os.makedirs(docs_dir, exist_ok=True)

            # Create README.md
            with open(os.path.join(docs_dir, "README.md"), "w", encoding="utf-8") as f:
                f.write(f"# {domain} Documentation\n\n")
                f.write(f"Documentation exported from {base_url}\n\n")
                f.write("## Contents\n\n")

            # Process each URL and create corresponding files
            for url, content in results.items():
                try:
                    # Create a suitable filename from the URL
                    parsed = urlparse(url)
                    path_parts = [p for p in parsed.path.split("/") if p]

                    if not path_parts:
                        path_parts = ["index"]

                    # Create subdirectories if needed
                    current_dir = docs_dir
                    for part in path_parts[:-1]:
                        current_dir = os.path.join(current_dir, part)
                        os.makedirs(current_dir, exist_ok=True)

                    # Create the markdown file
                    filename = path_parts[-1] + ".md"
                    file_path = os.path.join(current_dir, filename)

                    with open(file_path, "w", encoding="utf-8") as f:
                        # Add metadata at the top
                        f.write("---\n")
                        f.write(f"source: {url}\n")
                        f.write("---\n\n")
                        f.write(content)

                    # Update README with link
                    rel_path = os.path.relpath(file_path, docs_dir)
                    with open(
                        os.path.join(docs_dir, "README.md"), "a", encoding="utf-8"
                    ) as f:
                        f.write(f"- [{' > '.join(path_parts)}]({rel_path})\n")

                except Exception as e:
                    logger.error(f"Error processing URL {url}: {str(e)}")

            # Create a zip file
            zip_path = os.path.join(temp_dir, "documentation.zip")
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
                for root, _, files in os.walk(docs_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arc_name = os.path.relpath(file_path, temp_dir)
                        zf.write(file_path, arc_name)

            # Read the zip file
            with open(zip_path, "rb") as f:
                content = f.read()

            return Response(
                content=content,
                media_type="application/zip",
                headers={
                    "Content-Disposition": f'attachment; filename="{domain}_documentation.zip"'
                },
            )

    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/discover")
async def discover_docs(request: Request):
    try:
        data = await request.json()
        inputs = data.get("inputs", [])

        if not inputs:
            return JSONResponse({"error": "No inputs provided"}, status_code=400)

        doc_finder = DocFinder()
        all_urls = {}

        for input_str in inputs:
            input_str = input_str.strip()

            # Check if it's a GitHub URL/repo
            if (
                "github.com" in input_str
                or "/" in input_str
                and len(input_str.split("/")) == 2
            ):
                urls = await doc_finder.find_github_docs(input_str)
                for url_info in urls:
                    all_urls[url_info["url"]] = url_info

            # Check if it's a direct URL
            elif input_str.startswith(("http://", "https://")):
                all_urls[input_str] = {"url": input_str, "source": "Direct URL"}

            # Treat as package name
            else:
                package_info = await get_package_docs(input_str)
                if "docs" in package_info:
                    for doc_info in package_info["docs"]:
                        all_urls[doc_info["url"]] = doc_info
                elif "error" not in package_info:
                    # If no docs but no error, try DuckDuckGo search
                    ddg_results = await search_duckduckgo(f"{input_str} documentation")
                    for doc_info in ddg_results:
                        all_urls[doc_info["url"]] = doc_info

        return JSONResponse({"urls": all_urls})
    except Exception as e:
        logger.error(f"Discovery error: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/multi-library/analyze")
async def analyze_multi_library_project(request: Request):
    """Analyze multi-library project and generate unified documentation."""
    try:
        data = await request.json()
        project_type = data.get("project_type", "python")
        dependencies_file = data.get("dependencies_file", "")

        if not dependencies_file:
            return JSONResponse(
                {"error": "Dependencies file content is required"}, status_code=400
            )

        # Import required modules with error handling
        try:
            from src.processors.compatibility_checker import CompatibilityChecker
            from src.processors.dependency_parser import DependencyParser
            from src.processors.unified_doc_generator import (
                UnifiedDocumentationGenerator,
            )
            from src.visualizers.dependency_graph import DependencyGraphGenerator
        except ImportError as e:
            logger.error(f"Import error in multi-library endpoint: {e}")
            return JSONResponse(
                {"error": f"Module import failed: {str(e)}"}, status_code=500
            )

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

        # Get documentation URLs for each dependency
        documentation_urls = {}
        for dependency in dependencies:
            lib_name = dependency["name"]
            lib_type = dependency["type"]

            try:
                if lib_type == "python":
                    # Try PyPI first
                    package_info = await get_package_docs(lib_name)
                    if "docs" in package_info:
                        documentation_urls[lib_name] = package_info["docs"]
                    else:
                        # Fallback to DuckDuckGo search
                        ddg_results = await search_duckduckgo(
                            f"{lib_name} documentation"
                        )
                        documentation_urls[lib_name] = ddg_results[:3]
                else:
                    # Generic search for other types
                    ddg_results = await search_duckduckgo(f"{lib_name} documentation")
                    documentation_urls[lib_name] = ddg_results[:3]
            except Exception as e:
                logger.warning(f"Failed to get docs for {lib_name}: {e}")
                documentation_urls[lib_name] = []

        # Generate unified documentation
        doc_generator = UnifiedDocumentationGenerator()

        # Create mock library docs for unified generation
        library_docs = {}
        for lib_name in documentation_urls:
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

        return JSONResponse(
            {
                "status": "success",
                "dependencies": dependencies,
                "documentation_urls": documentation_urls,
                "unified_docs": unified_docs,
                "compatibility_report": compatibility_report,
                "dependency_graph": dependency_graph.to_dict(),
            }
        )

    except Exception as e:
        logger.error(f"Multi-library analysis failed: {e}")
        return JSONResponse({"error": f"Analysis failed: {str(e)}"}, status_code=500)


@app.get("/api/test")
async def test_endpoint():
    """Simple test endpoint to verify API routing works."""
    return JSONResponse({"status": "success", "message": "Test endpoint working"})


@app.post("/api/relevance/detect")
async def relevance_detection_endpoint(request: Request):
    """Content relevance detection endpoint."""
    try:
        data = await request.json()
        content = data.get("content", "")
        method = data.get("method", "hybrid")
        threshold = data.get("threshold", 0.6)

        if not content:
            return JSONResponse({"error": "Content is required"}, status_code=400)

        # Import relevance detection modules
        from src.processors.relevance_detection import (
            HybridRelevanceDetector,
            NLPRelevanceDetector,
            RuleBasedRelevanceDetector,
        )

        # Select detector based on method
        if method == "nlp":
            detector = NLPRelevanceDetector()
        elif method == "rule_based":
            detector = RuleBasedRelevanceDetector()
        else:  # hybrid
            detector = HybridRelevanceDetector()

        # Analyze content
        import time

        start_time = time.time()
        result = detector.is_documentation_relevant(content)
        processing_time = time.time() - start_time

        return JSONResponse(
            {
                "is_relevant": result.get("is_relevant", False),
                "confidence": result.get("confidence", result.get("score", 0.5)),
                "method_used": method,
                "processing_time": round(processing_time, 3),
                "reasoning": result.get("reasoning", ""),
                "threshold_used": threshold,
            }
        )

    except Exception as e:
        logger.error(f"Relevance detection error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/relevance/detect-batch")
async def batch_relevance_detection_endpoint(request: Request):
    """Batch content relevance detection endpoint."""
    try:
        data = await request.json()
        contents = data.get("contents", [])
        method = data.get("method", "rule_based")  # Use faster method for batch

        if not contents:
            return JSONResponse({"error": "Contents list is required"}, status_code=400)

        # Import relevance detection modules
        from src.processors.relevance_detection import (
            HybridRelevanceDetector,
            NLPRelevanceDetector,
            RuleBasedRelevanceDetector,
        )

        # Select detector based on method
        if method == "nlp":
            detector = NLPRelevanceDetector()
        elif method == "rule_based":
            detector = RuleBasedRelevanceDetector()
        else:  # hybrid
            detector = HybridRelevanceDetector()

        # Process all contents
        results = []
        for item in contents:
            content_id = item.get("id", "unknown")
            content = item.get("content", "")

            if content:
                result = detector.is_documentation_relevant(content)
                results.append(
                    {
                        "id": content_id,
                        "is_relevant": result.get("is_relevant", False),
                        "confidence": result.get(
                            "confidence", result.get("score", 0.5)
                        ),
                        "reasoning": result.get("reasoning", ""),
                    }
                )
            else:
                results.append(
                    {
                        "id": content_id,
                        "is_relevant": False,
                        "confidence": 0.0,
                        "reasoning": "Empty content",
                    }
                )

        return JSONResponse(
            {"results": results, "method_used": method, "total_processed": len(results)}
        )

    except Exception as e:
        logger.error(f"Batch relevance detection error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/search/semantic")
async def semantic_search_endpoint(request: Request):
    """Advanced semantic search endpoint."""
    try:
        data = await request.json()
        query = data.get("query", "")
        limit = data.get("limit", 5)
        filters = data.get("filters", {})

        if not query:
            return JSONResponse({"error": "Query is required"}, status_code=400)

        # Import search engine
        from src.search.semantic_search import SemanticSearchEngine

        # Create and use search engine (in production, this would be cached)
        search_engine = SemanticSearchEngine()

        # Mock documentation content for demo
        mock_docs = {
            "requests": {
                "content": "HTTP library for Python, built for human beings",
                "sections": [
                    {"title": "Quick Start", "content": "Making requests is simple"}
                ],
                "tags": ["http", "web", "python"],
                "difficulty": "beginner",
            },
            "fastapi": {
                "content": "Modern, fast web framework for building APIs with Python",
                "sections": [
                    {"title": "First Steps", "content": "Create FastAPI instance"}
                ],
                "tags": ["web", "api", "framework", "python"],
                "difficulty": "intermediate",
            },
        }

        # Index documents
        search_engine.index_documents(mock_docs)

        # Perform search
        results = search_engine.search(query, limit, filters)

        return JSONResponse(
            {
                "results": results,
                "total_count": len(results),
                "query": query,
                "query_time": 0.1,  # Mock query time
            }
        )

    except Exception as e:
        logger.error(f"Semantic search error: {e}")
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/start_crawl")
async def start_crawl(request: Request):
    """Start crawling the selected URLs."""
    try:
        # Get URLs from request body
        data = await request.json()
        logger.info(f"Received crawl request data: {data}")

        urls = data.get("urls", [])
        if not urls:
            return JSONResponse({"error": "No URLs provided"}, status_code=400)

        # Log additional configuration parameters if present
        backend_type = data.get("backend", "auto")
        max_depth = data.get("maxDepth", 3)
        advanced_options = data.get("advancedOptions", {})
        logger.info(
            f"Configuration: backend={backend_type}, max_depth={max_depth}, advanced_options={advanced_options}"
        )

        # Initialize backend selector and config
        selector = BackendSelector()
        crawl4ai_config = Crawl4AIConfig(
            max_retries=3,
            timeout=30.0,
            headers={"User-Agent": "Crawl4AI/1.0 Documentation Crawler"},
            follow_redirects=True,
            verify_ssl=False,  # Disable SSL verification since we had issues
            max_depth=max_depth,
        )
        Crawl4AIBackend(config=crawl4ai_config)

        results = []
        for url in urls:
            try:
                # Use create_url_info instead of normalize_url to get proper URL object
                url_info = create_url_info(url)
                if not url_info.is_valid:
                    results.append(
                        {
                            "url": url,
                            "status": "error",
                            "message": f"Invalid URL: {url_info.error_message}",
                        }
                    )
                    continue

                backend = await selector.select_backend(url)
                if not backend:
                    results.append(
                        {
                            "url": url,
                            "status": "error",
                            "message": "No suitable backend found",
                        }
                    )
                    continue

                # Start crawling
                result = await backend.crawl(url_info)

                # Process result
                if result.error:
                    results.append(
                        {"url": url, "status": "error", "message": result.error}
                    )
                else:
                    results.append(
                        {
                            "url": url,
                            "status": "success",
                            "message": "Successfully crawled",
                            "data": {
                                "content": result.content,
                                "metadata": result.metadata,
                            },
                        }
                    )

            except Exception as e:
                logger.error(f"Error during crawling: {str(e)}")
                results.append({"url": url, "status": "error", "message": str(e)})

        # Generate task ID for tracking
        import uuid

        task_id = str(uuid.uuid4())

        # Return response format that frontend expects
        return JSONResponse(
            {
                "status": "success",
                "message": "Scraping started",
                "task_id": task_id,
                "url": urls[0] if urls else None,
                "backend": backend_type,
                "results": results,
            }
        )

    except Exception as e:
        logger.error(f"Error during crawling: {str(e)}")
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)


@app.websocket("/ws/crawl")
async def crawl_websocket(websocket: WebSocket):
    """Handle WebSocket connections for real-time crawling updates."""
    try:
        await websocket.accept()
        logger.info("WebSocket connection accepted")

        async with socket_lock:
            active_websockets.add(websocket)

        try:
            while True:
                message = await websocket.receive_json()
                logger.info(f"Received WebSocket message: {message}")

                if message.get("type") == "crawl":
                    # Split the space-separated string into a list
                    if isinstance(message["urls"], str):
                        urls = message["urls"].split()
                    else:
                        urls = message["urls"]

                    # Clean and validate URLs
                    urls = [url.strip() for url in urls if url.strip()]

                    if not urls:
                        await websocket.send_json(
                            {"type": "error", "message": "No valid URLs provided"}
                        )
                        continue

                    logger.info(f"Starting crawl for URLs: {urls}")
                    await handle_crawl(websocket, urls)
                else:
                    logger.warning(f"Unknown message type: {message.get('type')}")
                    await websocket.send_json(
                        {"type": "error", "message": "Unknown message type"}
                    )

        except WebSocketDisconnect:
            logger.info("WebSocket disconnected")
            raise
        except Exception as e:
            logger.error(f"Error in WebSocket loop: {str(e)}")
            if websocket.client_state != WebSocketState.DISCONNECTED:
                await websocket.send_json(
                    {"type": "error", "message": f"Server error: {str(e)}"}
                )

    finally:
        async with socket_lock:
            if websocket in active_websockets:
                active_websockets.remove(websocket)
        logger.info("WebSocket connection closed and cleaned up")


async def handle_crawl(websocket: WebSocket, urls: list[str]):
    """Handle crawling for websocket connection."""
    try:
        # Initialize crawler
        backend_selector = BackendSelector()
        backend = await backend_selector.select_backend(None)

        for url in urls:
            try:
                # Send progress update
                await websocket.send_json(
                    {"type": "progress", "url": url, "status": "starting"}
                )

                # Crawl the URL
                result = await backend.crawl(url)

                if result.success:
                    # Store result
                    crawl_results[url] = result.content

                    # Send success update
                    await websocket.send_json(
                        {
                            "type": "progress",
                            "url": url,
                            "status": "completed",
                            "data": {
                                "content": result.content[
                                    :1000
                                ],  # First 1000 chars for preview
                                "metadata": result.metadata,
                            },
                        }
                    )
                else:
                    # Send error update
                    await websocket.send_json(
                        {
                            "type": "progress",
                            "url": url,
                            "status": "error",
                            "message": result.error or "Unknown error",
                        }
                    )

            except Exception as e:
                logger.error(f"Error crawling {url}: {str(e)}")
                await websocket.send_json(
                    {
                        "type": "progress",
                        "url": url,
                        "status": "error",
                        "message": str(e),
                    }
                )

        # Send completion message
        await websocket.send_json(
            {"type": "completed", "message": f"Finished crawling {len(urls)} URLs"}
        )

    except Exception as e:
        logger.error(f"Error in handle_crawl: {str(e)}")
        await websocket.send_json({"type": "error", "message": str(e)})


async def handle_scraping(websocket: WebSocket, urls: list[str]):
    """Handle scraping of URLs with real-time updates."""
    try:
        # Initialize crawler with configuration
        config = Config(
            max_pages=10,
            follow_links=True,
            concurrent_requests=5,
            extract_metadata=True,
            timeout=30.0,
            verify_ssl=False,
        )
        crawler = Crawler(config)

        total_urls = len(urls)
        results = []

        # Process URLs
        for idx, url in enumerate(urls, 1):
            try:
                # Send progress update
                await websocket.send_json(
                    {
                        "type": "progress",
                        "message": f"Processing URL {idx}/{total_urls}",
                        "url": url,
                        "progress": (idx / total_urls) * 100,
                    }
                )

                # Validate URL
                url_info = create_url_info(url)
                if not url_info.is_valid:
                    logger.warning(
                        f"Invalid URL skipped: {url} - {url_info.error_message}"
                    )
                    results.append(
                        {
                            "url": url,
                            "status": "error",
                            "message": f"Invalid URL: {url_info.error_message}",
                        }
                    )
                    continue

                # Normalize URL
                normalized_url = normalize_url(url)
                logger.info(f"Processing normalized URL: {normalized_url}")

                # Crawl URL with timeout and retries
                try:
                    result = await asyncio.wait_for(
                        crawler.crawl(normalized_url), timeout=30.0
                    )
                except asyncio.TimeoutError:
                    logger.error(f"Timeout crawling URL: {url}")
                    results.append(
                        {"url": url, "status": "error", "message": "Request timed out"}
                    )
                    continue

                # Process result
                if result.error:
                    logger.error(f"Crawl error for {url}: {result.error}")
                    results.append(
                        {"url": url, "status": "error", "message": result.error}
                    )
                else:
                    try:
                        # Clean and convert content
                        content = clean_and_convert_html(result.content, url)

                        # Store results
                        results.append(
                            {
                                "url": url,
                                "status": "success",
                                "content": content,
                                "metadata": result.metadata,
                            }
                        )
                        scraping_results[url] = content

                        # Send success update
                        await websocket.send_json(
                            {
                                "type": "success",
                                "url": url,
                                "message": "Processing completed",
                            }
                        )

                    except Exception as e:
                        logger.error(f"Error processing content for {url}: {str(e)}")
                        results.append(
                            {
                                "url": url,
                                "status": "error",
                                "message": f"Content processing error: {str(e)}",
                            }
                        )

            except Exception as e:
                logger.error(f"Error processing URL {url}: {str(e)}")
                results.append({"url": url, "status": "error", "message": str(e)})

            # Send progress update
            if websocket.client_state != WebSocketState.DISCONNECTED:
                await websocket.send_json(
                    {
                        "type": "progress",
                        "completed": idx,
                        "total": total_urls,
                        "progress": (idx / total_urls) * 100,
                    }
                )

        # Send final results
        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.send_json(
                {
                    "type": "complete",
                    "total_processed": total_urls,
                    "successful": len([r for r in results if r["status"] == "success"]),
                    "failed": len([r for r in results if r["status"] == "error"]),
                    "results": results,
                }
            )

    except Exception as e:
        logger.error(f"Error in handle_scraping: {str(e)}", exc_info=True)
        if websocket.client_state != WebSocketState.DISCONNECTED:
            await websocket.send_json(
                {"type": "error", "message": f"Server error: {str(e)}"}
            )
    try:
        if websocket.client_state == WebSocketState.DISCONNECTED:
            logger.error("WebSocket disconnected before crawl")
            return

        # Initialize crawler
        config = Config(
            max_depth=3, max_pages=100, follow_links=True, extract_metadata=True
        )
        crawler = Crawler(config)

        # Track crawled URLs and their content
        crawled_content = {}
        crawled_links = set()
        current_tasks = set()

        async def process_url(url: str):
            try:
                current_tasks.add(url)
                await websocket.send_json(
                    {"type": "update_tasks", "tasks": list(current_tasks)}
                )

                # Fetch and process content
                async with aiohttp.ClientSession() as session:
                    content = await fetch_url(url, session)
                    if not content:
                        return

                    # Clean and format content
                    formatted_content = clean_and_convert_html(content, url)

                    # Extract links
                    soup = BeautifulSoup(content, "html.parser")
                    links = []
                    for a in soup.find_all("a", href=True):
                        href = urljoin(url, a["href"])
                        if href not in crawled_links and href.startswith("http"):
                            links.append(
                                {
                                    "url": href,
                                    "text": a.get_text(strip=True),
                                    "type": "internal"
                                    if urlparse(url).netloc == urlparse(href).netloc
                                    else "external",
                                }
                            )
                            crawled_links.add(href)

                    # Store results
                    crawled_content[url] = {
                        "content": formatted_content,
                        "links": links,
                        "title": soup.title.string if soup.title else url,
                    }

                    # Send update
                    await websocket.send_json(
                        {
                            "type": "content_update",
                            "url": url,
                            "content": formatted_content,
                            "links": links,
                        }
                    )

            except Exception as e:
                logger.error(f"Error processing {url}: {str(e)}")
            finally:
                current_tasks.remove(url)
                await websocket.send_json(
                    {"type": "update_tasks", "tasks": list(current_tasks)}
                )

        # Process URLs concurrently
        tasks = [process_url(url) for url in urls]
        await asyncio.gather(*tasks)

        # Send final update
        await websocket.send_json(
            {
                "type": "crawl_complete",
                "stats": {
                    "urls_crawled": len(crawled_content),
                    "links_found": len(crawled_links),
                },
            }
        )

    except Exception as e:
        logger.error(f"Error in handle_crawl: {str(e)}")
        await websocket.send_json({"type": "error", "message": str(e)})


def get_crawler_config(url: str, url_info: dict) -> dict:
    """Get crawler configuration based on URL and info."""
    config = {
        "selectors": {"content": [], "ignore": []},
        "follow_patterns": [],
        "ignore_patterns": [],
    }

    # GitHub-specific configuration
    if "github.com" in url or url_info.get("source", "").startswith("GitHub"):
        config.update(
            {
                "selectors": {
                    "content": ["article.markdown-body", ".wiki-content"],
                    "ignore": [".file-navigation", ".commit-tease", ".pagehead"],
                },
                "follow_patterns": [
                    r"/blob/main/.*\.md$",
                    r"/tree/main/.*",
                    r"/wiki/.*",
                ],
                "ignore_patterns": [
                    r"/commit/",
                    r"/pulls/",
                    r"/issues/",
                    r"/actions/",
                ],
            }
        )

    # ReadTheDocs configuration
    elif any(pattern in url for pattern in [".readthedocs.io", ".readthedocs.org"]):
        config.update(
            {
                "selectors": {
                    "content": [".document", ".rst-content"],
                    "ignore": [".headerlink", ".sphinxsidebar"],
                }
            }
        )

    return config


def open_browser(port: int):
    """Open the browser after a short delay to ensure server is running."""
    # Only open browser if not running in headless/test environment
    if os.environ.get("NO_BROWSER") == "1" or os.environ.get("CI") == "1":
        return
    url = f"http://127.0.0.1:{port}"
    webbrowser.open(url)


if __name__ == "__main__":
    port = find_free_port()
    print(f"Starting server on port {port}")

    # Schedule browser opening
    Timer(1.5, open_browser, args=[port]).start()

    # Start the server
    uvicorn.run(app, host="127.0.0.1", port=port)
