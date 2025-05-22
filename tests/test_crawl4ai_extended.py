import aiohttp

import pytest
import asyncio
from unittest.mock import patch, AsyncMock
import pytest_asyncio  # For async fixtures
from urllib.parse import urljoin
from typing import List, Dict, Any
from bs4 import BeautifulSoup

import src.backends.crawl4ai # Import the module itself for patching
from src.utils.helpers import URLInfo # Keep URLInfo import for type hinting if needed elsewhere
from src.utils.url.factory import create_url_info # Import the factory function
from src.backends.base import CrawlResult
from src.backends.crawl4ai import Crawl4AIBackend, Crawl4AIConfig # Add Crawl4AIConfig import

# test_utils/mocks.py
class DummyRequestInfo:
    def __init__(self, url: str):
        self.real_url = url
        self.url = url

class MockResponse:

    def __init__(self, url: str, status: int, html: str, headers: Dict[str, str] = None):
        self.url = url
        self.status = status
        self._html = html
        self.headers = headers or {}

    async def text(self) -> str:
        return self._html

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

    def raise_for_status(self) -> None:
        if not (200 <= self.status < 300):
            # Create a request_info object with real_url attribute
            request_info = DummyRequestInfo(self.url)
            raise aiohttp.ClientResponseError(
                request_info=request_info,
                history=None,
                status=self.status,
                message=f"HTTP {self.status} for {self.url}",
                headers=self.headers
            )

def test_raise_for_status() -> None:
    response = MockResponse("http://example.com", 404, "<html></html>")
    with pytest.raises(aiohttp.ClientResponseError) as excinfo:
        response.raise_for_status()
    assert "HTTP 404" in str(excinfo.value)

class MockClientSession:
    def __init__(self, responses: Dict[str, Any]): # Allow list/exception for retry
        self.responses = responses
        self.closed = False
        self.requests = []
        self._call_counts = {} # Track call counts per URL

    async def get(self, url: str, **kwargs):
        self._call_counts[url] = self._call_counts.get(url, 0) + 1 # Increment call count
        self.requests.append((url, kwargs))
        response_or_list = self.responses.get(url)

        if isinstance(response_or_list, list):
            # Handle list of responses for retry tests
            call_index = self._call_counts[url] - 1
            if call_index < len(response_or_list):
                 response = response_or_list[call_index]
                 if isinstance(response, Exception): # Raise exception if it's one
                     raise response
                 return response
            else:
                 # Default if list is exhausted (shouldn't happen in well-defined tests)
                 return MockResponse(url, 404, "", {})
        elif response_or_list:
             # Handle single response case
             if isinstance(response_or_list, Exception): # Raise exception if it's one
                 raise response_or_list
             return response_or_list
        else:
             # Default 404 if URL not in mock setup
             return MockResponse(url, 404, "", {})


    async def close(self):
        self.closed = True

    def get_call_count(self, url: str) -> int:
        """Helper to get call count for a specific URL."""
        return self._call_counts.get(url, 0)


@pytest_asyncio.fixture
async def mock_html() -> str:
    return """
    <html>
        <body>
            <a href="/page1">Page 1</a>
            <a href="https://example.com/page2">Page 2</a>
            <a href="../page3">Page 3</a>
            <a href="page4">Page 4</a>
        </body>
    </html>
    """

@pytest_asyncio.fixture
async def mock_responses(mock_html: str) -> Dict[str, Any]: # Allow list/exception
    base_url = "https://example.com"
    responses = {
        base_url: MockResponse(
            base_url,
            200,
            mock_html,
            {"content-type": "text/html"}
        ),
        # Add the normalized URL with trailing slash
        f"{base_url}/": MockResponse(
            f"{base_url}/",
            200,
            mock_html,
            {"content-type": "text/html"}
        ),
        f"{base_url}/page1": MockResponse(
            f"{base_url}/page1",
            200,
            "<html><body>Page 1</body></html>",
            {"content-type": "text/html"}
        ),
        f"{base_url}/page2": MockResponse(
            f"{base_url}/page2",
            200,
            "<html><body>Page 2</body></html>",
            {"content-type": "text/html"}
        ),
        f"{base_url}/page3": MockResponse( # Add mock for page3
            f"{base_url}/page3",
            200,
            "<html><body>Page 3</body></html>",
            {"content-type": "text/html"}
        ),
        f"{base_url}/page4": MockResponse( # Add mock for page4
            f"{base_url}/page4",
            200,
            "<html><body>Page 4</body></html>",
            {"content-type": "text/html"}
        ),
        # Add entries for test_urls fixture in test_crawler.py
        f"{base_url}/doc1": MockResponse(
            f"{base_url}/doc1",
            200,
            "<html><body>Doc 1 Content</body></html>",
            {"content-type": "text/html"}
        ),
        f"{base_url}/doc2": MockResponse(
            f"{base_url}/doc2",
            200,
            "<html><body>Doc 2 Content</body></html>",
            {"content-type": "text/html"}
        ),
        f"{base_url}/doc3": MockResponse(
            f"{base_url}/doc3",
            200,
            "<html><body>Doc 3 Content</body></html>",
            {"content-type": "text/html"}
        ),
         # Add entries for error propagation test
        "https://nonexistent.example.com": MockResponse("https://nonexistent.example.com", 404, "", {}), # Mock 404
        "https://example.com/notfound": MockResponse("https://example.com/notfound", 404, "", {}),
        "https://example.com/error": MockResponse("https://example.com/error", 500, "", {}), # Simulate server error
         # Entry for retry test
        "https://example.com/unstable": [
            Exception("Temporary failure 1"),
            Exception("Temporary failure 2"),
            MockResponse("https://example.com/unstable", 200, "<html>Success</html>", {})
        ]
    }
    return responses

@pytest_asyncio.fixture
async def mock_session(mock_responses: Dict[str, Any]) -> MockClientSession: # Changed type hint
    return MockClientSession(mock_responses)

@pytest_asyncio.fixture
async def crawl4ai_backend(monkeypatch, mock_session: MockClientSession) -> Crawl4AIBackend:
    config = Crawl4AIConfig(
        max_retries=2,
        timeout=10.0,
        headers={"User-Agent": "Test/1.0"},
        rate_limit=1000.0,  # High rate limit for fast tests by default
        max_depth=3,
        concurrent_requests=2
    )
    backend = Crawl4AIBackend(config=config)

    # Patch the session creation
    async def mock_create_session():
        return mock_session

    monkeypatch.setattr(backend, "_create_session", mock_create_session)

    # Reset metrics directly before yielding for test isolation
    backend.metrics = {
        "pages_crawled": 0,
        "successful_requests": 0,
        "failed_requests": 0,
        "total_crawl_time": 0.0,
        "cached_pages": 0,
        "total_pages": 0,
        "start_time": 0.0,
        "end_time": 0.0,
        "success_rate": 0.0,
        "average_response_time": 0.0,
    }

    # Yield the backend instance to the test
    yield backend

    # Cleanup: Close the backend session after the test
    await backend.close()

@pytest.mark.asyncio
async def test_crawl_with_urlinfo(crawl4ai_backend: Crawl4AIBackend) -> None:
    """Test crawling with URLInfo object."""
    url_info = create_url_info(url="https://example.com")
    result = await crawl4ai_backend.crawl(url_info)

    assert result is not None
    assert result.url == url_info.normalized_url 
    assert result.status == 200
    assert isinstance(result.content, dict)
    assert "html" in result.content

@pytest.mark.skip(reason="Link following is handled by the main Crawler, not the backend directly.")
@pytest.mark.asyncio
async def test_crawl_depth_first(crawl4ai_backend: Crawl4AIBackend) -> None:
    """Test depth-first crawling behavior."""
    url = "https://example.com"
    url_info = create_url_info(url) 
    result = await crawl4ai_backend.crawl(url_info) 

    requests = crawl4ai_backend._session.requests
    assert len(requests) >= 3  

    request_urls = [req[0] for req in requests]
    assert request_urls[0] == url  

    child_urls = request_urls[1:]
    path_depths = [len(url.split("/")) for url in child_urls]
    assert path_depths == sorted(path_depths, reverse=True)

@patch('asyncio.sleep', new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_rate_limiting_application(mock_sleep: AsyncMock, crawl4ai_backend: Crawl4AIBackend) -> None:
    """Test that rate limiting logic is applied (sleep is called) without actual delay."""
    crawl4ai_backend.config.rate_limit = 0.1 
    urls = ["https://example.com/page1", "https://example.com/page2"]

    results = await asyncio.gather(*[
        crawl4ai_backend.crawl(create_url_info(url)) for url in urls
    ])
    
    assert all(result.status == 200 for result in results)
    assert mock_sleep.called 

@patch('asyncio.sleep', new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_concurrent_request_limit(mock_sleep: AsyncMock, crawl4ai_backend: Crawl4AIBackend) -> None:
    """Test enforcement of concurrent request limit without actual delay.
    This test tracks concurrent task count via a wrapped crawl method to verify concurrency limits."""
    crawl4ai_backend.config.rate_limit = 0.1 
    crawl4ai_backend._last_request_time = 0.0 # Ensure a predictable start for rate limiter
    mock_sleep.return_value = None 

    urls = [
        "https://example.com/page1",
        "https://example.com/page2",
        "https://example.com/page4", 
        "https://example.com/page3" 
    ]
    
    original_acquire = crawl4ai_backend._processing_semaphore.acquire
    max_concurrent_tasks = 0
    current_concurrent_tasks = 0

    async def tracking_acquire(*args, **kwargs):
        nonlocal max_concurrent_tasks, current_concurrent_tasks
        current_concurrent_tasks += 1
        max_concurrent_tasks = max(max_concurrent_tasks, current_concurrent_tasks)
        try:
            return await original_acquire(*args, **kwargs)
        finally:
            current_concurrent_tasks -= 1
    
    with patch.object(crawl4ai_backend._processing_semaphore, 'acquire', side_effect=tracking_acquire):
        results = await asyncio.gather(*[
            crawl4ai_backend.crawl(create_url_info(url)) for url in urls
        ])
        assert all(isinstance(result, CrawlResult) for result in results) 
        assert all(result.status == 200 for result in results if result) 

    assert max_concurrent_tasks <= crawl4ai_backend.config.concurrent_requests
    assert mock_sleep.called

@pytest.mark.asyncio
async def test_url_normalization(crawl4ai_backend: Crawl4AIBackend) -> None:
    """Test URL normalization with different input formats."""
    test_cases = [
        ("https://example.com", "https://example.com"),
        ("https://example.com/", "https://example.com/"),
        ("https://example.com/page1?param=value", "https://example.com/page1?param=value"),
        ("https://example.com/page1#section", "https://example.com/page1"),
        ("https://example.com/page1?param=value#section", "https://example.com/page1?param=value"),
        ("https://example.com/page%20with%20spaces", "https://example.com/page%20with%20spaces"),
        ("https://example.com/search?q=%22quoted%22", "https://example.com/search?q=%22quoted%22"),
        ("https://user:pass@example.com", "https://user:pass@example.com"),
        ("https://user:pass@example.com/page1", "https://user:pass@example.com/page1"),
        ("https://example.com:8080", "https://example.com:8080"),
        ("https://example.com:8080/page1", "https://example.com:8080/page1"),
        ("https://EXAMPLE.com/PAGE1", "https://example.com/PAGE1"),
        ("HTTPS://example.com/page1", "https://example.com/page1"),
        ("https://example.com/./page1", "https://example.com/page1"),
        ("https://example.com/page1/.", "https://example.com/page1"), 
    ]

    for input_url, expected_url in test_cases:
        url_info = create_url_info(url=input_url)
        result = await crawl4ai_backend.crawl(url_info)
        assert result.url == expected_url

@pytest.mark.asyncio
async def test_error_propagation(crawl4ai_backend: Crawl4AIBackend) -> None:
    """Test proper error propagation through the crawling chain."""
    error_cases = [
        ("https://nonexistent.example.com", 404),  
        ("https://example.com/notfound", 404),     
        ("https://example.com/error", 500),        
    ]

    for url, expected_status in error_cases: 
        url_info_err = create_url_info(url)
        result = await crawl4ai_backend.crawl(url_info_err) 
        assert result.status == 0
        assert result.error is not None

@pytest.mark.asyncio
async def test_retry_behavior(crawl4ai_backend: Crawl4AIBackend, monkeypatch) -> None: 
    """Test retry behavior with failing requests."""
    url = "https://example.com/unstable"
    attempts = []
    await crawl4ai_backend._ensure_session()
    mock_session_instance = crawl4ai_backend._session

    async def side_effect(*args, **kwargs):
        attempts.append(1)
        if len(attempts) < 3:
            raise Exception("Temporary failure")
        return MockResponse(url, 200, "<html>Success</html>", {})

    mock_session_get = AsyncMock(side_effect=side_effect)
    monkeypatch.setattr(mock_session_instance, "get", mock_session_get)

    url_info_unstable = create_url_info(url)
    result = await crawl4ai_backend.crawl(url_info=url_info_unstable)

    assert len(attempts) == 3 
    assert result.status == 200 
    assert result.error is None
    assert mock_session_get.call_count == 3

@pytest.mark.asyncio
async def test_metrics_accuracy(crawl4ai_backend: Crawl4AIBackend) -> None: # Removed mocker
    """Test accuracy of metrics collection."""
    url = "https://example.com"
    start_time = 1.0
    end_time = 2.5
    dummy_stray_call_time_val = 0.0 # Value for the single stray call

    class TimeMockState:
        def __init__(self):
            self.call_count = 0
            self.stray_time_val = dummy_stray_call_time_val
            self.start_time_val = start_time
            self.end_time_val = end_time

        def mock_time_function(self):
            self.call_count += 1
            if self.call_count == 1:
                return self.stray_time_val
            elif self.call_count == 2:
                return self.start_time_val
            return self.end_time_val

    time_mock_state = TimeMockState()
    url_info_metrics = create_url_info(url)

    with patch.object(crawl4ai_backend, '_wait_rate_limit', new_callable=AsyncMock), \
         patch('src.backends.crawl4ai.time.time', side_effect=time_mock_state.mock_time_function):
        result = await crawl4ai_backend.crawl(url_info_metrics)
        metrics = crawl4ai_backend.get_metrics()

        crawl_duration = end_time - start_time
        assert abs(metrics["start_time"] - start_time) < 0.01, f"Expected start_time {start_time}, got {metrics['start_time']}"
        assert metrics["end_time"] is not None
        assert abs(metrics["end_time"] - end_time) < 0.01, f"Expected end_time {end_time}, got {metrics['end_time']}"
        assert metrics["total_crawl_time"] >= 0
        assert abs(metrics["total_crawl_time"] - crawl_duration) < 0.01, f"Expected total_crawl_time {crawl_duration}, got {metrics['total_crawl_time']}"
        assert metrics["successful_requests"] >= 1
        assert metrics["failed_requests"] >= 0

@pytest.mark.asyncio
async def test_resource_cleanup(crawl4ai_backend: Crawl4AIBackend, mocker) -> None:
    """Test proper cleanup of resources with mocked session."""
    url = "https://example.com"

    mock_session = mocker.AsyncMock()
    mock_session.close = mocker.AsyncMock()
    mock_session.closed = False 
    crawl4ai_backend._session = mock_session

    crawl4ai_backend._processing_semaphore = mocker.AsyncMock()
    crawl4ai_backend._processing_semaphore._value = crawl4ai_backend.config.concurrent_requests
    crawl4ai_backend._rate_limiter = mocker.AsyncMock()
    crawl4ai_backend._rate_limiter.locked = mocker.Mock(return_value=False)

    url_info_cleanup = create_url_info(url)
    await crawl4ai_backend.crawl(url_info=url_info_cleanup, config=crawl4ai_backend.config) 

    await crawl4ai_backend.close()

    mock_session.close.assert_called_once()
    assert crawl4ai_backend._session is None

    assert crawl4ai_backend._processing_semaphore._value == crawl4ai_backend.config.concurrent_requests
    assert not crawl4ai_backend._rate_limiter.locked()

    await crawl4ai_backend._ensure_session()
    assert crawl4ai_backend._session is not None
    await crawl4ai_backend._ensure_session()
    assert crawl4ai_backend._session is not None 
@pytest.mark.parametrize("input_url,expected", [
    (
        "https://docs.python.org/3/",
        {
            "original": "https://docs.python.org/3/",
            "normalized": "https://docs.python.org/3/",
            "scheme": "https",
            "netloc": "docs.python.org",
            "path": "/3/",
            "is_valid": True
        }
    ),
    (
        "https://docs.python.org",
        {
            "original": "https://docs.python.org",
            "normalized": "https://docs.python.org", 
            "scheme": "https",
            "netloc": "docs.python.org",
            "path": "", 
            "is_valid": True
        }
    ), 
    (   
        "https://docs.python.org:8080/3/?query=test#fragment",
        {
            "original": "https://docs.python.org:8080/3/?query=test#fragment",
            "normalized": "https://docs.python.org:8080/3/?query=test", 
            "scheme": "https",
            "netloc": "docs.python.org:8080",
            "path": "/3/",
            "is_valid": True
        }
    ),
    (
        "https://user:password@docs.python.org/3/",
        {
            "original": "https://user:password@docs.python.org/3/",
            "normalized": "https://user:password@docs.python.org/3/", 
            "scheme": "https",
            "netloc": "user:password@docs.python.org",
            "path": "/3/",
            "is_valid": False 
        }
    ),
    (
        "https://docs.python.org/path with spaces/",
        {
            "original": "https://docs.python.org/path with spaces/",
            "normalized": "https://docs.python.org/path%20with%20spaces/", 
            "scheme": "https",
            "netloc": "docs.python.org",
            "path": "/path%20with%20spaces/", 
            "is_valid": True
        }
    ),
    (
        "https://docs.python.org/3/../4/",
        {
            "original": "https://docs.python.org/3/../4/",
            "normalized": "https://docs.python.org/3/../4/", 
            "scheme": "https",
            "netloc": "docs.python.org",
            "path": "/3/../4/", 
            "is_valid": False 
        }
    ),
    (
        "invalid-url",
        {
            "original": "invalid-url",
            "normalized": "invalid-url",
            "scheme": "",
            "netloc": "", 
            "path": "invalid-url",
            "is_valid": False
        }
    ),
])
def test_url_info_initialization(input_url: str, expected: dict) -> None:
    """Test URLInfo initialization from string."""
    url_info = create_url_info(input_url)
    assert url_info.raw_url == expected["original"]
    assert url_info.normalized_url == expected["normalized"]
    assert url_info.scheme == expected["scheme"]
    assert url_info.netloc == expected["netloc"]
    assert url_info.path == expected["path"]
    assert url_info.is_valid == expected["is_valid"]
def test_url_info_hashable() -> None:
    """Test that URLInfo objects are hashable and can be used in sets."""
    url1 = create_url_info("https://docs.python.org/3/")
    url2 = create_url_info("https://docs.python.org/3")
    url3 = create_url_info("https://docs.python.org/3/")

    url_set = {url1, url2, url3}
    assert len(url_set) == 2  

def test_url_info_immutable() -> None:
    """Test that URLInfo objects are immutable."""
    url = create_url_info("https://docs.python.org/3/")
    with pytest.raises(AttributeError):
        url.new_attribute = "something-else"
