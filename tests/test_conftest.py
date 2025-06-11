"""Tests for conftest.py fixtures and mocks."""

import pytest

from tests.conftest import MockFailureBackend, MockSuccessBackend


def test_mock_success_backend():
    """Test that MockSuccessBackend can be instantiated."""
    backend = MockSuccessBackend()
    assert backend.name == "mock_success_backend"


def test_mock_failure_backend():
    """Test that MockFailureBackend can be instantiated."""
    backend = MockFailureBackend()
    assert backend.name == "mock_failure_backend"
    assert not backend.crawl_called
    assert not backend.validate_called
    assert not backend.process_called


@pytest.mark.asyncio
async def test_mock_success_backend_crawl():
    """Test the crawl method of MockSuccessBackend."""
    backend = MockSuccessBackend()

    # Import here to avoid potential circular imports
    from src.utils.url.factory import create_url_info

    url_info = create_url_info("https://example.com/test")

    result = await backend.crawl(url_info)
    assert result.status == 200
    assert result.content_type == "text/html"
    # URL ending with /test returns "Discovered Page" content
    assert "Discovered Page" in result.content.get("html", "")
    assert not result.error
    assert len(result.documents) > 0


@pytest.mark.asyncio
async def test_mock_failure_backend_crawl():
    """Test the crawl method of MockFailureBackend."""
    backend = MockFailureBackend()

    # Import here to avoid potential circular imports
    from src.utils.url.factory import create_url_info

    url_info = create_url_info("https://example.com/test")

    result = await backend.crawl(url_info)
    assert result.status == 500
    assert result.error == "Simulated failure"
    assert backend.crawl_called
    assert not result.documents


def test_sample_html_factory(sample_html_factory):
    """Test that sample_html_factory produces expected HTML."""
    html = sample_html_factory(
        title="Custom Title",
        heading="Custom Heading",
        paragraph="Custom paragraph text.",
        link="/custom-link",
    )

    assert "Custom Title" in html
    assert "Custom Heading" in html
    assert "Custom paragraph text." in html
    assert "/custom-link" in html


def test_soup_fixture(soup):
    """Test that soup fixture creates a BeautifulSoup object."""
    assert soup is not None
    assert soup.title.text.strip() == "Test Document"
    assert soup.h1.text.strip() == "Test Heading"


def test_processor_config(processor_config):
    """Test that processor_config fixture creates a valid ProcessorConfig."""
    assert processor_config.max_content_length == 10000
    assert processor_config.min_content_length == 10
    assert processor_config.extract_code_blocks is True


@pytest.mark.asyncio
async def test_content_processor(content_processor):
    """Test that content_processor fixture creates a mocked ContentProcessor."""
    assert content_processor is not None
    # Test that the mock returns the expected processed content
    from src.backends.base import CrawlResult

    # Create a minimal CrawlResult for testing
    crawl_result = CrawlResult(
        url="https://example.com/test",
        content={"html": "<html><body>Test</body></html>"},
        status=200,
        content_type="text/html",
        metadata={"title": "Test Page"},  # Adding required metadata field
    )

    processed = await content_processor.process(crawl_result)
    assert processed.content.get("formatted_content") == "Processed content"
    assert processed.metadata.get("title") == "Sample Document"
