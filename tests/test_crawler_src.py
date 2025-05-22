"""Tests for DocumentationCrawler class in src.crawler."""

import pytest
from unittest.mock import MagicMock, patch
import asyncio
from src.crawler import DocumentationCrawler, CrawlerConfig
from src.backends.selector import BackendSelector
from src.processors.content_processor import ContentProcessor
from src.processors.quality_checker import QualityChecker
from src.organizers.doc_organizer import DocumentOrganizer
from src.utils.search import DuckDuckGoSearch
from src.utils.url.factory import create_url_info

class TestDocumentationCrawlerInit:
    """Tests for DocumentationCrawler initialization."""

    def test_init_with_defaults(self):
        """Test initialization with default values."""
        crawler = DocumentationCrawler()
        
        # Check that config is defaulted correctly
        assert crawler.config is not None
        assert isinstance(crawler.config, CrawlerConfig)
        
        # Check that core components are initialized
        assert crawler.backend_selector is not None
        assert isinstance(crawler.backend_selector, BackendSelector)
        assert crawler.content_processor is not None
        assert crawler.quality_checker is not None
        assert crawler.document_organizer is not None
        
        # Check that HTTP backend was registered
        assert len(crawler.backend_selector._backends) > 0
        assert 'http' in crawler.backend_selector._backends
        
        # Check that internal state was initialized correctly
        assert crawler._crawled_urls == set()
        assert crawler.client_session is None

    def test_init_with_custom_config(self):
        """Test initialization with custom configuration."""
        custom_config = CrawlerConfig(concurrent_requests=5, user_agent="Custom Agent")
        crawler = DocumentationCrawler(config=custom_config)
        
        # Check that config was correctly applied
        assert crawler.config is custom_config
        assert crawler.config.concurrent_requests == 5
        assert crawler.config.user_agent == "Custom Agent"

    def test_init_with_custom_components(self):
        """Test initialization with custom components."""
        mock_backend_selector = MagicMock(spec=BackendSelector)
        mock_content_processor = MagicMock(spec=ContentProcessor)
        mock_quality_checker = MagicMock(spec=QualityChecker)
        mock_document_organizer = MagicMock(spec=DocumentOrganizer)
        
        crawler = DocumentationCrawler(
            backend_selector=mock_backend_selector,
            content_processor=mock_content_processor,
            quality_checker=mock_quality_checker,
            document_organizer=mock_document_organizer
        )
        
        # Check that components were correctly applied
        assert crawler.backend_selector is mock_backend_selector
        assert crawler.content_processor is mock_content_processor
        assert crawler.quality_checker is mock_quality_checker
        assert crawler.document_organizer is mock_document_organizer

class TestDocumentationCrawlerMethods:
    """Tests for DocumentationCrawler methods."""

    def test_find_links_recursive(self):
        """Test _find_links_recursive method."""
        crawler = DocumentationCrawler()
        
        # Test with empty structure
        assert crawler._find_links_recursive({}) == []
        assert crawler._find_links_recursive([]) == []
        
        # Test with a simple link
        link_element = {
            "type": "link",
            "href": "https://example.com",
            "text": "Example"
        }
        assert crawler._find_links_recursive(link_element) == ["https://example.com"]
        
        # Test with a nested structure containing links
        nested_structure = {
            "type": "document",
            "elements": [
                {
                    "type": "paragraph",
                    "children": [
                        {
                            "type": "text",
                            "value": "Some text"
                        },
                        {
                            "type": "link_inline",
                            "href": "https://example.com/docs",
                            "text": "Docs"
                        }
                    ]
                },
                {
                    "type": "link",
                    "href": "https://example.com/api",
                    "text": "API"
                }
            ]
        }
        
        links = crawler._find_links_recursive(nested_structure)
        assert len(links) == 2
        assert "https://example.com/docs" in links
        assert "https://example.com/api" in links

    def test_should_crawl_url(self):
        """Test _should_crawl_url method."""
        crawler = DocumentationCrawler()
        target = crawler.CrawlTarget(url="https://example.com")
        
        # Test with invalid URL
        invalid_url = create_url_info("invalid://example.com")
        assert not crawler._should_crawl_url(invalid_url, target)
        
        # Test with already crawled URL
        valid_url = create_url_info("https://example.com/page")
        crawler._crawled_urls.add(valid_url.normalized_url)
        assert not crawler._should_crawl_url(valid_url, target)
