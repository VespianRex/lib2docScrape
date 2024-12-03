#!/usr/bin/env python3
"""Run the Crawl4AI testing interface."""

from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from starlette.websockets import WebSocketState
from starlette.responses import HTMLResponse, JSONResponse, FileResponse, StreamingResponse
from starlette.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn
from pathlib import Path
import json
from typing import List, Dict, Any, Optional
import asyncio
from src.backends.crawl4ai import Crawl4AIBackend as Crawler, Crawl4AIConfig as Config, CrawlResult
from src.backends.selector import BackendSelector
from src.backends.crawl4ai import Crawl4AIConfig, Crawl4AIBackend
from src.utils.helpers import normalize_url
import base64
from urllib.parse import unquote, urlparse
import socket
import webbrowser
from contextlib import closing
from threading import Timer
import html2text
from bs4 import BeautifulSoup
import re
import logging
import aiohttp
import tempfile
import zipfile
import os
from urllib.parse import urlparse
import shutil
import requests
from packaging import version
import ssl
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('crawler.log')
    ]
)
logger = logging.getLogger(__name__)

def find_free_port():
    """Find a free port to use for the server."""
    with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as s:
        s.bind(('', 0))
        s.listen(1)
        port = s.getsockname()[1]
        return port

class DomainConfig:
    """Configuration for specific documentation domains."""
    def __init__(self, domain: str, patterns: List[str] = None, selectors: List[str] = None):
        self.domain = domain
        self.content_patterns = patterns or []  # URL patterns to match
        self.content_selectors = selectors or []  # CSS selectors for main content

# Common documentation site configurations
DOMAIN_CONFIGS = {
    'promptfoo.dev': DomainConfig(
        domain='promptfoo.dev',
        patterns=[r'/docs/intro$', r'/docs/.*'],
        selectors=['.theme-doc-markdown', '.markdown']
    ),
    'firecrawl.dev': DomainConfig(
        domain='firecrawl.dev',
        patterns=[r'/docs/intro$', r'/docs/.*'],
        selectors=['.theme-doc-markdown', '.markdown']
    ),
    'docs.python.org': DomainConfig(
        domain='docs.python.org',
        patterns=[r'/3/.*'],
        selectors=['.body', '.document']
    ),
    'docs.pytest.org': DomainConfig(
        domain='docs.pytest.org',
        patterns=[r'/en/.*'],
        selectors=['.document', '.body']
    ),
    'fastapi.tiangolo.com': DomainConfig(
        domain='fastapi.tiangolo.com',
        patterns=[r'/.*'],
        selectors=['.md-content__inner', '.markdown-body']
    ),
    'react.dev': DomainConfig(
        domain='react.dev',
        patterns=[r'/learn.*', r'/reference.*', r'/blog.*'],
        selectors=['.markdown', '.article-content']
    ),
    'docs.github.com': DomainConfig(
        domain='docs.github.com',
        patterns=[r'/.*'],
        selectors=['.markdown-body', '.article-body']
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
    # Add scheme if missing
    if not url.startswith(('http://', 'https://')):
        url = 'https://' + url
    
    try:
        parsed = urlparse(url)
        domain = parsed.netloc
        path = parsed.path.rstrip('/')
        
        # Get domain-specific config
        config = DOMAIN_CONFIGS.get(domain)
        if config:
            # Check if URL matches any domain-specific patterns
            for pattern in config.content_patterns:
                if re.search(pattern + '$', path):
                    return url
            
            # Apply domain-specific normalization
            if domain == 'promptfoo.dev' and path == '/docs':
                return 'https://promptfoo.dev/docs/intro'
            elif domain == 'firecrawl.dev' and path == '/docs':
                return 'https://firecrawl.dev/docs/intro'
            elif domain == 'docs.python.org' and path == '/3':
                return 'https://docs.python.org/3/tutorial/index.html'
            elif domain == 'react.dev' and path == '':
                return 'https://react.dev/learn'
    except Exception as e:
        logger.error(f"Error normalizing URL {url}: {str(e)}")
    
    return url

def clean_and_convert_html(html: str, url: str) -> str:
    """Clean HTML with domain-specific handling."""
    soup = BeautifulSoup(html, 'html.parser')
    
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
            'main',
            'article',
            '[role="main"]',
            '.main-content',
            '.content',
            '.document',
            '.markdown-body',
            '.md-content',
            '#content',
            '.post-content',
            '.entry-content',
            '.theme-doc-markdown',
            '.prose',
            '.docusaurus-highlight-code-line',
            '.docs-markdown',
            '.documentation-content',
            '.sphinx-content',
            '.rst-content',
            '.section',
            '.body',
            '.page-content',
            '.main-container',
            '.doc-content'
        ]
        
        for selector in content_selectors:
            main_content = soup.select_one(selector)
            if main_content:
                break
    
    if not main_content:
        main_content = soup.body or soup
    
    # Remove unwanted elements
    for element in main_content.select('script, style, iframe, nav, footer, header, .sidebar, .navigation-menu'):
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

async def fetch_url(url: str, session: aiohttp.ClientSession, max_retries: int = 3, base_delay: float = 1.0) -> tuple[str, int]:
    """Fetch URL content with improved error handling and retry logic."""
    url = normalize_url(url)
    delay = base_delay
    
    logger.info(f"Normalized URL: {url}")
    
    for attempt in range(max_retries):
        try:
            logger.debug(f"Attempt {attempt + 1}/{max_retries}")
            async with session.get(url, ssl=False if url.startswith('https://localhost') else True) as response:
                if response.status == 404:
                    # Try common alternatives
                    alternatives = [
                        f"https://promptfoo.dev/docs/intro",  # Direct try for promptfoo
                        url + '/intro',
                        url.rstrip('/') + '/introduction',
                        url.rstrip('/') + '/getting-started',
                        re.sub(r'/docs/?$', '/docs/intro', url),
                        re.sub(r'/docs/?$', '/docs/getting-started', url)
                    ]
                    
                    for alt_url in alternatives:
                        logger.info(f"Trying alternative URL: {alt_url}")
                        try:
                            async with session.get(alt_url, ssl=False if alt_url.startswith('https://localhost') else True) as alt_response:
                                if alt_response.status == 200:
                                    return await alt_response.text(), alt_response.status
                        except Exception as e:
                            logger.debug(f"Failed to fetch alternative URL {alt_url}: {str(e)}")
                            continue
                
                return await response.text(), response.status
                
        except (aiohttp.ClientError, asyncio.TimeoutError) as e:
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
            'readthedocs.io': lambda pkg: f"https://{pkg}.readthedocs.io/",
            'readthedocs.org': lambda pkg: f"https://{pkg}.readthedocs.org/",
            'github.io': lambda pkg: f"https://{pkg}.github.io/",
        }
        
        self.package_registries = {
            'pypi': 'https://pypi.org/pypi/{package}/json',
            'npm': 'https://registry.npmjs.org/{package}',
        }
    
    async def find_github_docs(self, repo_path: str) -> List[Dict[str, str]]:
        """Find documentation for a GitHub repository."""
        try:
            # Clean the repo path
            repo_path = repo_path.replace('github.com/', '').replace('https://', '').replace('http://', '')
            api_url = f"https://api.github.com/repos/{repo_path}"
            
            headers = {}
            if os.environ.get('GITHUB_TOKEN'):
                headers['Authorization'] = f"token {os.environ['GITHUB_TOKEN']}"
            
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
                    if repo_data.get('has_pages'):
                        docs_urls.append({
                            'url': f"https://{repo_data['owner']['login']}.github.io/{repo_data['name']}/",
                            'source': 'GitHub Pages'
                        })
                    
                    # Check common doc locations
                    doc_paths = ['docs/', 'doc/', 'documentation/', 'wiki/']
                    for path in doc_paths:
                        check_url = f"https://github.com/{repo_path}/tree/main/{path}"
                        async with session.get(check_url) as doc_response:
                            if doc_response.status == 200:
                                docs_urls.append({
                                    'url': check_url,
                                    'source': f'GitHub {path}'
                                })
                    
                    return docs_urls
        except Exception as e:
            logger.error(f"Error finding GitHub docs: {str(e)}")
            return []

async def get_package_docs(package_name: str) -> Dict[str, Any]:
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
                    info = data['info']
                    
                    # Project URLs
                    if 'project_urls' in info and info['project_urls']:
                        for label, url in info['project_urls'].items():
                            if url and any(keyword in label.lower() for keyword in ['doc', 'wiki', 'guide', 'manual']):
                                docs.append({
                                    'url': url,
                                    'source': f'PyPI {label}'
                                })
                    
                    # Documentation URL
                    if info.get('docs_url'):
                        docs.append({
                            'url': info['docs_url'],
                            'source': 'PyPI Documentation'
                        })
                    
                    # Project Homepage
                    if info.get('home_page'):
                        docs.append({
                            'url': info['home_page'],
                            'source': 'Project Homepage'
                        })
                    
                    # ReadTheDocs
                    rtd_url = f"https://{package_name}.readthedocs.io/"
                    try:
                        async with session.get(rtd_url) as rtd_response:
                            if rtd_response.status == 200:
                                docs.append({
                                    'url': rtd_url,
                                    'source': 'ReadTheDocs'
                                })
                    except:
                        pass

                    # DuckDuckGo Search
                    ddg_results = await search_duckduckgo(f"{package_name} python documentation")
                    docs.extend(ddg_results)

                    # Remove duplicates while preserving order
                    seen_urls = set()
                    unique_docs = []
                    for doc in docs:
                        if doc['url'] not in seen_urls:
                            seen_urls.add(doc['url'])
                            unique_docs.append(doc)
                    docs = unique_docs

                    if docs:
                        return {
                            'name': package_name,
                            'version': info.get('version', 'unknown'),
                            'summary': info.get('summary', ''),
                            'docs': docs
                        }
                    
                    logger.warning(f"No documentation found for {package_name}")
                    return {
                        'name': package_name,
                        'error': 'No documentation found'
                    }
                
                # If PyPI fails, try DuckDuckGo
                docs = await search_duckduckgo(f"{package_name} documentation")
                if docs:
                    return {
                        'name': package_name,
                        'docs': docs
                    }
                
                logger.error(f"Package {package_name} not found on PyPI")
                return {
                    'name': package_name,
                    'error': 'Package not found on PyPI'
                }

    except Exception as e:
        logger.error(f"Error fetching docs for {package_name}: {str(e)}")
        return {
            'name': package_name,
            'error': str(e)
        }

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Global variables for WebSocket management
active_websockets: set[WebSocket] = set()
socket_lock = asyncio.Lock()

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/crawl")
async def crawl(request: Request):
    try:
        data = await request.json()
        url = data.get("url", "")
        max_pages = data.get("max_pages", 10)
        
        if not url:
            return {"error": "URL is required"}
        
        # Create a new crawler instance
        config = Config(
            max_pages=max_pages,
            follow_links=True,
            concurrent_requests=5
        )
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
                        f.write(f"---\n")
                        f.write(f"source: {url}\n")
                        f.write(f"---\n\n")
                        f.write(content)
                    
                    # Update README with link
                    rel_path = os.path.relpath(file_path, docs_dir)
                    with open(os.path.join(docs_dir, "README.md"), "a", encoding="utf-8") as f:
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
                }
            )
    
    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/discover")
async def discover_docs(request: Request):
    try:
        data = await request.json()
        inputs = data.get('inputs', [])
        
        if not inputs:
            return JSONResponse({"error": "No inputs provided"}, status_code=400)
        
        doc_finder = DocFinder()
        all_urls = {}
        
        for input_str in inputs:
            input_str = input_str.strip()
            
            # Check if it's a GitHub URL/repo
            if 'github.com' in input_str or '/' in input_str and len(input_str.split('/')) == 2:
                urls = await doc_finder.find_github_docs(input_str)
                for url_info in urls:
                    all_urls[url_info['url']] = url_info
            
            # Check if it's a direct URL
            elif input_str.startswith(('http://', 'https://')):
                all_urls[input_str] = {
                    'url': input_str,
                    'source': 'Direct URL'
                }
            
            # Treat as package name
            else:
                urls = await doc_finder.find_package_docs(input_str)
                for url_info in urls:
                    all_urls[url_info['url']] = url_info
        
        return JSONResponse({
            "urls": all_urls
        })
    except Exception as e:
        logger.error(f"Discovery error: {str(e)}")
        return JSONResponse({"error": str(e)}, status_code=500)

@app.post("/start_crawl")
async def start_crawl(request: Request):
    """Start crawling the selected URLs."""
    try:
        # Get URLs from request body
        data = await request.json()
        urls = data.get('urls', [])
        if not urls:
            return JSONResponse({"error": "No URLs provided"}, status_code=400)

        # Initialize backend selector and config
        selector = BackendSelector()
        crawl4ai_config = Crawl4AIConfig(
            max_retries=3,
            timeout=30.0,
            headers={"User-Agent": "Crawl4AI/1.0 Documentation Crawler"},
            follow_redirects=True,
            verify_ssl=False,  # Disable SSL verification since we had issues
            max_depth=5
        )
        crawl4ai_backend = Crawl4AIBackend(config=crawl4ai_config)

        results = []
        for url in urls:
            try:
                url_info = normalize_url(url)
                if not url_info.is_valid:
                    results.append({
                        'url': url,
                        'status': 'error',
                        'message': 'Invalid URL'
                    })
                    continue

                backend = await selector.select_backend(url)
                if not backend:
                    results.append({
                        'url': url,
                        'status': 'error',
                        'message': 'No suitable backend found'
                    })
                    continue

                # Start crawling
                result = await backend.crawl(url_info)
                
                # Process result
                if result.error:
                    results.append({
                        'url': url,
                        'status': 'error',
                        'message': result.error
                    })
                else:
                    results.append({
                        'url': url,
                        'status': 'success',
                        'message': 'Successfully crawled',
                        'data': {
                            'content': result.content,
                            'metadata': result.metadata
                        }
                    })

            except Exception as e:
                logger.error(f"Crawl error: {str(e)}")
                results.append({
                    'url': url,
                    'status': 'error',
                    'message': str(e)
                })

        return JSONResponse({
            'status': 'completed',
            'results': results
        })

    except Exception as e:
        logger.error(f"Crawl error: {str(e)}")
        return JSONResponse({
            'status': 'error',
            'message': str(e)
        }, status_code=500)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """Handle WebSocket connections."""
    try:
        await websocket.accept()
        logger.info("WebSocket connection accepted")
        
        async with socket_lock:
            active_websockets.add(websocket)
        
        try:
            while True:
                message = await websocket.receive_json()
                logger.info(f"Received WebSocket message: {message}")
                
                if message.get('type') == 'crawl':
                    # Split the space-separated string into a list
                    if isinstance(message['urls'], str):
                        urls = message['urls'].split()
                    else:
                        urls = message['urls']
                    
                    # Clean and validate URLs
                    urls = [url.strip() for url in urls if url.strip()]
                    
                    if not urls:
                        await websocket.send_json({
                            "type": "error",
                            "message": "No valid URLs provided"
                        })
                        continue
                        
                    logger.info(f"Starting crawl for URLs: {urls}")
                    await handle_crawl(websocket, urls)
                else:
                    logger.warning(f"Unknown message type: {message.get('type')}")
                    await websocket.send_json({
                        "type": "error",
                        "message": "Unknown message type"
                    })
                    
        except WebSocketDisconnect:
            logger.info("WebSocket disconnected")
            raise
        except Exception as e:
            logger.error(f"Error in WebSocket loop: {str(e)}")
            if websocket.client_state != WebSocketState.DISCONNECTED:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Server error: {str(e)}"
                })
    
    finally:
        async with socket_lock:
            if websocket in active_websockets:
                active_websockets.remove(websocket)
        logger.info("WebSocket connection closed and cleaned up")

async def handle_crawl(websocket: WebSocket, urls: List[str]):
    """Handle crawling of URLs with real-time updates."""
    try:
        if websocket.client_state == WebSocketState.DISCONNECTED:
            logger.error("WebSocket disconnected before crawl")
            return

        # Initialize crawler
        config = Config(
            max_depth=3,
            max_pages=100,
            follow_links=True,
            extract_metadata=True
        )
        crawler = Crawler(config)
        
        # Track crawled URLs and their content
        crawled_content = {}
        crawled_links = set()
        current_tasks = set()
        
        async def process_url(url: str):
            try:
                current_tasks.add(url)
                await websocket.send_json({
                    "type": "update_tasks",
                    "tasks": list(current_tasks)
                })
                
                # Fetch and process content
                async with aiohttp.ClientSession() as session:
                    content = await fetch_url(url, session)
                    if not content:
                        return
                    
                    # Clean and format content
                    formatted_content = clean_and_convert_html(content, url)
                    
                    # Extract links
                    soup = BeautifulSoup(content, 'html.parser')
                    links = []
                    for a in soup.find_all('a', href=True):
                        href = urljoin(url, a['href'])
                        if href not in crawled_links and href.startswith('http'):
                            links.append({
                                'url': href,
                                'text': a.get_text(strip=True),
                                'type': 'internal' if urlparse(url).netloc == urlparse(href).netloc else 'external'
                            })
                            crawled_links.add(href)
                    
                    # Store results
                    crawled_content[url] = {
                        'content': formatted_content,
                        'links': links,
                        'title': soup.title.string if soup.title else url
                    }
                    
                    # Send update
                    await websocket.send_json({
                        "type": "content_update",
                        "url": url,
                        "content": formatted_content,
                        "links": links
                    })
                    
            except Exception as e:
                logger.error(f"Error processing {url}: {str(e)}")
            finally:
                current_tasks.remove(url)
                await websocket.send_json({
                    "type": "update_tasks",
                    "tasks": list(current_tasks)
                })
        
        # Process URLs concurrently
        tasks = [process_url(url) for url in urls]
        await asyncio.gather(*tasks)
        
        # Send final update
        await websocket.send_json({
            "type": "crawl_complete",
            "stats": {
                "urls_crawled": len(crawled_content),
                "links_found": len(crawled_links)
            }
        })
        
    except Exception as e:
        logger.error(f"Error in handle_crawl: {str(e)}")
        await websocket.send_json({
            "type": "error",
            "message": str(e)
        })

def get_crawler_config(url: str, url_info: Dict) -> Dict:
    """Get crawler configuration based on URL and info."""
    config = {
        'selectors': {
            'content': [],
            'ignore': []
        },
        'follow_patterns': [],
        'ignore_patterns': []
    }
    
    # GitHub-specific configuration
    if 'github.com' in url or url_info.get('source', '').startswith('GitHub'):
        config.update({
            'selectors': {
                'content': ['article.markdown-body', '.wiki-content'],
                'ignore': ['.file-navigation', '.commit-tease', '.pagehead'],
            },
            'follow_patterns': [
                r'/blob/main/.*\.md$',
                r'/tree/main/.*',
                r'/wiki/.*',
            ],
            'ignore_patterns': [
                r'/commit/',
                r'/pulls/',
                r'/issues/',
                r'/actions/',
            ]
        })
    
    # ReadTheDocs configuration
    elif any(pattern in url for pattern in ['.readthedocs.io', '.readthedocs.org']):
        config.update({
            'selectors': {
                'content': ['.document', '.rst-content'],
                'ignore': ['.headerlink', '.sphinxsidebar'],
            }
        })
    
    return config

def open_browser(port: int):
    """Open the browser after a short delay to ensure server is running."""
    url = f"http://127.0.0.1:{port}"
    webbrowser.open(url)

if __name__ == "__main__":
    port = find_free_port()
    print(f"Starting server on port {port}")
    
    # Schedule browser opening
    Timer(1.5, open_browser, args=[port]).start()
    
    # Start the server
    uvicorn.run(app, host="127.0.0.1", port=port)