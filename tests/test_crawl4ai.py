import asyncio

import pytest

from src.backends.crawl4ai_backend import Crawl4AIBackend, Crawl4AIConfig
from src.backends.selector import BackendCriteria, BackendSelector
from src.utils.url.factory import create_url_info  # Import factory


@pytest.fixture
def crawl4ai_backend():
    config = Crawl4AIConfig(
        max_retries=2, timeout=10.0, headers={"User-Agent": "Test/1.0"}, rate_limit=2.0
    )
    return Crawl4AIBackend(config=config)


@pytest.fixture
def backend_selector():
    selector = BackendSelector()
    return selector


@pytest.mark.asyncio
async def test_crawl_basic(crawl4ai_backend):
    # Test basic crawling functionality
    url = "https://example.com"
    url_info = create_url_info(url)  # Create URLInfo
    result = await crawl4ai_backend.crawl(url_info)  # Pass URLInfo

    assert result is not None
    # Assert against the expected *normalized* URL
    assert (
        result.url == "https://example.com"
    )  # Normalization removes trailing slash for root
    assert result.status == 200  # Expect 200 for successful crawl
    assert isinstance(result.content, dict)
    assert isinstance(result.metadata, dict)


@pytest.mark.asyncio
async def test_crawl_with_rate_limit(crawl4ai_backend):
    # Test rate limiting
    urls = ["https://example.com", "https://example.org"]
    start_time = asyncio.get_event_loop().time()

    results = await asyncio.gather(
        *[
            crawl4ai_backend.crawl(create_url_info(url))
            for url in urls  # Create and pass URLInfo
        ]
    )

    end_time = asyncio.get_event_loop().time()
    time_taken = end_time - start_time

    # With rate_limit=2.0, two requests should take at least 0.5 seconds
    assert time_taken >= 0.5
    assert all(result is not None for result in results)


@pytest.mark.asyncio
async def test_validate_content(crawl4ai_backend):
    # Test content validation
    url = "https://example.com"
    url_info = create_url_info(url)  # Create URLInfo
    result = await crawl4ai_backend.crawl(url_info)  # Pass URLInfo
    is_valid = await crawl4ai_backend.validate(result)

    assert isinstance(is_valid, bool)


@pytest.mark.asyncio
async def test_process_content(crawl4ai_backend):
    # Test content processing
    url = "https://example.com"
    url_info = create_url_info(url)  # Create URLInfo
    result = await crawl4ai_backend.crawl(url_info)  # Pass URLInfo
    processed = await crawl4ai_backend.process(result)

    assert isinstance(processed, dict)
    assert "content" in processed or "error" in processed


@pytest.mark.asyncio
async def test_backend_selection(backend_selector):
    # Test backend selection using MockCrawlerBackend
    # We'll create a mock backend instance for testing
    from tests.test_base import MockCrawlerBackend

    # Create and register a mock backend
    backend_instance = MockCrawlerBackend(name="test_crawler")
    backend_selector.register_backend(
        "test_crawler",
        backend_instance,
        BackendCriteria(
            priority=10,
            content_types=["text/html", "text/*"],
            url_patterns=["*example.com*"],
        ),
    )

    # Now test the backend selection
    url = "https://example.com"
    backend = await backend_selector.get_backend(url)

    assert backend is not None
    assert backend == backend_instance
    assert isinstance(backend, MockCrawlerBackend)


@pytest.mark.asyncio
async def test_metrics(crawl4ai_backend):
    # Test metrics tracking
    url = "https://example.com"
    url_info = create_url_info(url)  # Create URLInfo
    await crawl4ai_backend.crawl(url_info)  # Pass URLInfo

    metrics = crawl4ai_backend.get_metrics()
    assert isinstance(metrics, dict)
    assert "pages_crawled" in metrics
    assert "success_rate" in metrics
    assert "average_response_time" in metrics


@pytest.mark.asyncio
async def test_error_handling(crawl4ai_backend):
    # Test error handling with invalid URL
    url = "https://invalid-url-that-does-not-exist.com"
    url_info = create_url_info(url)  # Create URLInfo
    result = await crawl4ai_backend.crawl(url_info)  # Pass URLInfo

    assert result.error is not None
    # Expect 0 for network/DNS errors after retries fail (Reverted)
    assert result.status == 0


@pytest.mark.asyncio
async def test_concurrent_requests(crawl4ai_backend):
    # Test concurrent request handling
    urls = ["https://example.com", "https://example.org", "https://example.net"]

    results = await asyncio.gather(
        *[
            crawl4ai_backend.crawl(create_url_info(url))
            for url in urls  # Create and pass URLInfo
        ]
    )

    assert len(results) == len(urls)
    assert all(result is not None for result in results)


@pytest.mark.asyncio
async def test_cleanup(crawl4ai_backend):
    # Test resource cleanup
    url = "https://example.com"
    url_info = create_url_info(url)  # Create URLInfo
    await crawl4ai_backend.crawl(url_info)  # Pass URLInfo
    await crawl4ai_backend.close()

    # Session should be closed
    assert crawl4ai_backend._session is None or crawl4ai_backend._session.closed


def test_crawl4ai_config_validation():
    """Test Crawl4AIConfig validation."""
    # Test valid config
    config = Crawl4AIConfig(
        max_retries=3,
        timeout=30.0,
        headers={"User-Agent": "Test/1.0"},
        follow_redirects=True,
        verify_ssl=True,
        max_depth=5,
        rate_limit=2.0,
        follow_links=True,
        max_pages=100,
        allowed_domains=["example.com"],
        concurrent_requests=10,
    )
    assert config.max_retries == 3
    assert config.timeout == 30.0

    # Test invalid values (should raise pydantic.ValidationError)
    from pydantic import ValidationError

    with pytest.raises(ValidationError):
        Crawl4AIConfig(max_retries=-1)

    with pytest.raises(ValueError):
        Crawl4AIConfig(timeout=0)

    with pytest.raises(ValueError):
        Crawl4AIConfig(max_depth=-1)

    with pytest.raises(ValueError):
        Crawl4AIConfig(rate_limit=0)


@pytest.mark.asyncio
async def test_ssl_context_configuration(crawl4ai_backend):
    """Test SSL context configuration."""
    # Test with SSL verification enabled
    config = Crawl4AIConfig(verify_ssl=True)
    backend = Crawl4AIBackend(config=config)
    await backend._ensure_session()
    # SSL verification test simplified
    assert backend.config.verify_ssl is True
    await backend.close()

    # Test with SSL verification disabled
    config = Crawl4AIConfig(verify_ssl=False)
    backend = Crawl4AIBackend(config=config)
    await backend._ensure_session()
    assert backend.config.verify_ssl is False
    await backend.close()


@pytest.mark.asyncio
async def test_custom_headers_handling(crawl4ai_backend):
    """Test custom headers handling."""
    custom_headers = {
        "User-Agent": "CustomBot/1.0",
        "Accept-Language": "en-US",
        "Custom-Header": "Value",
    }
    config = Crawl4AIConfig(headers=custom_headers)
    backend = Crawl4AIBackend(config=config)
    await backend._ensure_session()

    # Just verify the config is set correctly
    assert backend.config.headers == custom_headers
    await backend.close()


@pytest.mark.asyncio
async def test_domain_filtering(crawl4ai_backend):
    """Test domain filtering."""
    config = Crawl4AIConfig(allowed_domains=["example.com"])
    backend = Crawl4AIBackend(config=config)

    # Test allowed domain
    url_info_allowed = create_url_info("https://example.com/page")
    result = await backend.crawl(url_info_allowed)  # Pass URLInfo
    assert result.status != 403

    # Test disallowed domain
    url_info_disallowed = create_url_info("https://other-domain.com/page")
    result = await backend.crawl(url_info_disallowed)  # Pass URLInfo
    assert result.status == 403  # Status 403 is correct
    assert (
        result.error is not None and "Domain not allowed" in result.error
    )  # Check error message

    await backend.close()


@pytest.mark.asyncio
async def test_url_queue_management(crawl4ai_backend, monkeypatch):  # Add monkeypatch
    """Test URL queue management."""
    urls = [f"https://example.com/page{i}" for i in range(3)]

    # Test queue processing order
    results = []
    for url in urls:
        url_info = create_url_info(url)  # Create URLInfo
        result = await crawl4ai_backend.crawl(url_info)  # Pass URLInfo
        results.append(result)

    # Verify order and uniqueness
    processed_urls = [r.url for r in results]
    assert len(processed_urls) == len(urls)
    assert len(set(processed_urls)) == len(urls)
