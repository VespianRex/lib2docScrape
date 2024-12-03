import pytest
from unittest.mock import patch, MagicMock
import asyncio

from src.crawler import DocumentationCrawler
from src.processors.content_processor import ContentProcessor
from src.processors.quality_checker import QualityChecker
from src.backends.crawl4ai import Crawl4AIBackend
from src.utils.helpers import URLProcessor, RateLimiter

@pytest.mark.asyncio
async def test_full_crawl_pipeline():
    """Test the complete crawling pipeline with all components."""
    # Initialize components
    url_processor = URLProcessor()
    rate_limiter = RateLimiter(requests_per_second=2)
    content_processor = ContentProcessor()
    quality_checker = QualityChecker()
    backend = Crawl4AIBackend(rate_limiter=rate_limiter)
    
    crawler = DocumentationCrawler(
        backend=backend,
        content_processor=content_processor,
        quality_checker=quality_checker
    )
    
    # Mock HTTP responses
    mock_responses = {
        "https://example.com": """
            <html>
                <body>
                    <h1>Documentation</h1>
                    <p>Main content</p>
                    <a href="https://example.com/page1">Page 1</a>
                    <a href="https://example.com/page2">Page 2</a>
                </body>
            </html>
        """,
        "https://example.com/page1": """
            <html>
                <body>
                    <h1>Page 1</h1>
                    <p>Content with code:</p>
                    <pre><code>def example():
                        pass</code></pre>
                </body>
            </html>
        """,
        "https://example.com/page2": """
            <html>
                <body>
                    <h1>Page 2</h1>
                    <p>Content with list:</p>
                    <ul>
                        <li>Item 1</li>
                        <li>Item 2</li>
                    </ul>
                </body>
            </html>
        """
    }
    
    async def mock_fetch(url, *args, **kwargs):
        return mock_responses.get(url, "")
    
    with patch.object(backend, '_fetch', side_effect=mock_fetch):
        result = await crawler.crawl("https://example.com", max_depth=2)
        
        # Check crawled content
        assert len(result.crawled_pages) == 3
        assert "https://example.com" in result.crawled_pages
        assert "https://example.com/page1" in result.crawled_pages
        assert "https://example.com/page2" in result.crawled_pages
        
        # Check content processing
        main_page = result.crawled_pages["https://example.com"]
        assert "Documentation" in main_page.processed_content['main']
        assert "Main content" in main_page.processed_content['main']
        
        # Check code handling
        page1 = result.crawled_pages["https://example.com/page1"]
        assert "def example():" in page1.raw_content
        
        # Check list handling
        page2 = result.crawled_pages["https://example.com/page2"]
        assert "Item 1" in page2.processed_content['main']
        assert "Item 2" in page2.processed_content['main']
        
        # Check quality issues
        assert isinstance(result.quality_report, dict)
        assert all(isinstance(issues, list) for issues in result.quality_report.values())

@pytest.mark.asyncio
async def test_error_handling_integration():
    """Test error handling across components."""
    crawler = DocumentationCrawler()
    
    # Test invalid URL
    with pytest.raises(ValueError):
        await crawler.crawl("not_a_url")
    
    # Test network error
    async def mock_fetch_error(*args, **kwargs):
        raise ConnectionError("Network error")
    
    with patch.object(crawler.backend, '_fetch', side_effect=mock_fetch_error):
        result = await crawler.crawl("https://example.com")
        assert len(result.failed_urls) == 1
        assert "https://example.com" in result.failed_urls
        assert isinstance(result.errors["https://example.com"], ConnectionError)

@pytest.mark.asyncio
async def test_rate_limiting_integration():
    """Test rate limiting across components."""
    rate_limiter = RateLimiter(requests_per_second=2)
    backend = Crawl4AIBackend(rate_limiter=rate_limiter)
    crawler = DocumentationCrawler(backend=backend)
    
    # Mock successful responses
    async def mock_fetch(*args, **kwargs):
        return "<html><body>Test content</body></html>"
    
    with patch.object(backend, '_fetch', side_effect=mock_fetch):
        start_time = asyncio.get_event_loop().time()
        
        # Crawl multiple pages
        result = await crawler.crawl(
            "https://example.com",
            max_depth=1,
            max_pages=5
        )
        
        end_time = asyncio.get_event_loop().time()
        elapsed = end_time - start_time
        
        # Should take at least 2 seconds for 5 pages at 2 req/sec
        assert elapsed >= 2.0
        assert len(result.crawled_pages) == 5

@pytest.mark.asyncio
async def test_content_processing_integration():
    """Test content processing integration with quality checking."""
    content_processor = ContentProcessor()
    quality_checker = QualityChecker()
    crawler = DocumentationCrawler(
        content_processor=content_processor,
        quality_checker=quality_checker
    )
    
    # Test content with various elements
    content = """
    <html>
        <body>
            <h1>Test Document</h1>
            <p>Regular paragraph</p>
            <pre><code>def test():
                pass</code></pre>
            <div class="warning">Warning message</div>
            <table>
                <tr><td>Cell 1</td><td>Cell 2</td></tr>
            </table>
        </body>
    </html>
    """
    
    async def mock_fetch(*args, **kwargs):
        return content
    
    with patch.object(crawler.backend, '_fetch', side_effect=mock_fetch):
        result = await crawler.crawl("https://example.com")
        
        processed = result.crawled_pages["https://example.com"]
        
        # Check content processing
        assert "Test Document" in processed.processed_content['main']
        assert "Regular paragraph" in processed.processed_content['main']
        assert "def test():" in processed.raw_content
        assert "Warning message" in processed.processed_content['main']
        
        # Check quality issues
        quality_issues = result.quality_report["https://example.com"]
        assert isinstance(quality_issues, list)
        
        # Verify metadata
        assert processed.metadata['has_code_blocks'] is True
        assert processed.metadata['has_tables'] is True
