"""Integration tests for the documentation crawler system."""

import asyncio
import os
from typing import Dict, List, Set

import pytest
from bs4 import BeautifulSoup

from src.backends.crawl4ai import Crawl4AIBackend, Crawl4AIConfig
from src.backends.selector import BackendCriteria, BackendSelector
from src.crawler import CrawlerConfig, CrawlTarget, DocumentationCrawler
from src.organizers.doc_organizer import DocumentOrganizer, OrganizationConfig
from src.processors.content_processor import ContentProcessor, ProcessorConfig
from src.processors.quality_checker import QualityChecker, QualityConfig


@pytest.fixture
def test_html_dir(tmp_path) -> str:
    """Create temporary directory with test HTML files."""
    html_dir = tmp_path / "test_docs"
    html_dir.mkdir()
    
    # Create index page
    index_html = """
    <html>
        <head>
            <title>Test Documentation</title>
            <meta name="description" content="Test documentation site">
        </head>
        <body>
            <h1>Test Documentation</h1>
            <nav>
                <ul>
                    <li><a href="api.html">API Reference</a></li>
                    <li><a href="guide.html">User Guide</a></li>
                    <li><a href="examples.html">Examples</a></li>
                </ul>
            </nav>
        </body>
    </html>
    """
    
    # Create API page
    api_html = """
    <html>
        <head>
            <title>API Reference</title>
            <meta name="description" content="API documentation">
        </head>
        <body>
            <h1>API Reference</h1>
            <h2>Endpoints</h2>
            <pre><code>GET /api/v1/docs</code></pre>
            <a href="index.html">Back to Index</a>
        </body>
    </html>
    """
    
    # Create guide page
    guide_html = """
    <html>
        <head>
            <title>User Guide</title>
            <meta name="description" content="User guide">
        </head>
        <body>
            <h1>User Guide</h1>
            <h2>Getting Started</h2>
            <p>This is a guide to get you started.</p>
            <pre><code class="language-python">
            import example
            example.run()
            </code></pre>
            <a href="index.html">Back to Index</a>
        </body>
    </html>
    """
    
    # Create examples page
    examples_html = """
    <html>
        <head>
            <title>Examples</title>
            <meta name="description" content="Code examples">
        </head>
        <body>
            <h1>Examples</h1>
            <h2>Basic Example</h2>
            <pre><code class="language-python">
            def hello():
                print("Hello, World!")
            </code></pre>
            <a href="index.html">Back to Index</a>
        </body>
    </html>
    """
    
    # Write files
    (html_dir / "index.html").write_text(index_html)
    (html_dir / "api.html").write_text(api_html)
    (html_dir / "guide.html").write_text(guide_html)
    (html_dir / "examples.html").write_text(examples_html)
    
    return str(html_dir)


@pytest.fixture
def integrated_crawler(test_html_dir: str) -> DocumentationCrawler:
    """Create fully integrated crawler instance."""
    # Configure backend
    backend = Crawl4AIBackend(
        config=Crawl4AIConfig(
            max_retries=2,
            timeout=5.0,
            headers={"User-Agent": "TestCrawler/1.0"}
        )
    )
    
    # Configure backend selector
    selector = BackendSelector()
    selector.register_backend(
        backend,
        BackendCriteria(
            priority=100,
            content_types=["text/html"],
            url_patterns=["*"],
            max_load=0.8,
            min_success_rate=0.7
        )
    )
    
    # Configure content processor
    processor = ContentProcessor(
        config=ProcessorConfig(
            allowed_tags=[
                "h1", "h2", "h3", "p", "pre", "code",
                "a", "ul", "li", "nav"
            ],
            preserve_whitespace_elements=["pre", "code"],
            code_languages=["python"],
            max_heading_level=3,
            max_content_length=10000,
            min_content_length=10
        )
    )
    
    # Configure quality checker
    checker = QualityChecker(
        config=QualityConfig(
            min_content_length=50,
            max_content_length=10000,
            min_headings=1,
            max_heading_depth=3,
            min_internal_links=1,
            max_broken_links_ratio=0.1,
            required_metadata_fields={"title", "description"}
        )
    )
    
    # Configure document organizer
    organizer = DocumentOrganizer(
        config=OrganizationConfig(
            min_similarity_score=0.3,
            max_versions_to_keep=3,
            category_rules={
                "api": ["api", "reference", "endpoint"],
                "guide": ["guide", "tutorial", "getting started"],
                "example": ["example", "sample", "demo"]
            }
        )
    )
    
    # Create and return crawler
    return DocumentationCrawler(
        config=CrawlerConfig(
            concurrent_requests=2,
            requests_per_second=10.0,
            max_retries=2,
            request_timeout=5.0
        ),
        backend_selector=selector,
        content_processor=processor,
        quality_checker=checker,
        document_organizer=organizer
    )


@pytest.mark.asyncio
async def test_full_site_crawl(
    integrated_crawler: DocumentationCrawler,
    test_html_dir: str
):
    """Test crawling a complete documentation site."""
    # Create crawl target
    target = CrawlTarget(
        url=f"file://{test_html_dir}/index.html",
        depth=2,
        follow_external=False,
        content_types=["text/html"],
        exclude_patterns=[],
        required_patterns=[".html"],
        max_pages=10
    )
    
    # Perform crawl
    result = await integrated_crawler.crawl(target)
    
    # Verify crawl statistics
    assert result.stats.pages_crawled > 0
    assert result.stats.successful_crawls > 0
    assert result.stats.failed_crawls == 0
    
    # Verify documents were processed
    assert len(result.documents) > 0
    
    # Verify document categorization
    categories = set()
    for doc_id in result.documents:
        doc = integrated_crawler.document_organizer.documents[doc_id]
        categories.add(doc.category)
    
    assert "api" in categories
    assert "guide" in categories
    assert "example" in categories


@pytest.mark.asyncio
async def test_content_processing_pipeline(
    integrated_crawler: DocumentationCrawler,
    test_html_dir: str
):
    """Test the complete content processing pipeline."""
    target = CrawlTarget(
        url=f"file://{test_html_dir}/guide.html",
        depth=1,
        max_pages=1
    )
    
    result = await integrated_crawler.crawl(target)
    assert len(result.documents) == 1
    
    doc_id = result.documents[0]
    doc = integrated_crawler.document_organizer.documents[doc_id]
    
    # Verify content processing
    assert doc.title == "User Guide"
    assert doc.category == "guide"
    assert len(doc.versions) == 1
    
    # Verify code block processing
    version = doc.versions[-1]
    assert "python" in str(version.changes).lower()
    assert "example.run()" in str(version.changes)


@pytest.mark.asyncio
async def test_quality_checks(
    integrated_crawler: DocumentationCrawler,
    test_html_dir: str
):
    """Test quality checking during crawl."""
    target = CrawlTarget(
        url=f"file://{test_html_dir}/api.html",
        depth=1,
        max_pages=1
    )
    
    result = await integrated_crawler.crawl(target)
    
    # Verify quality metrics
    assert len(result.metrics) > 0
    for doc_id, metrics in result.metrics.items():
        assert metrics.content_length > 0
        assert metrics.readability_score >= 0
        assert metrics.heading_structure_score >= 0


@pytest.mark.asyncio
async def test_document_organization(
    integrated_crawler: DocumentationCrawler,
    test_html_dir: str
):
    """Test document organization and relationships."""
    # Crawl all pages
    target = CrawlTarget(
        url=f"file://{test_html_dir}/index.html",
        depth=2,
        max_pages=10
    )
    
    result = await integrated_crawler.crawl(target)
    
    # Create a collection
    collection_id = integrated_crawler.document_organizer.create_collection(
        "Test Documentation",
        "Complete test documentation set",
        result.documents
    )
    
    # Verify collection
    collection = integrated_crawler.document_organizer.collections[collection_id]
    assert len(collection.documents) == len(result.documents)
    
    # Test document relationships
    for doc_id in result.documents:
        related = integrated_crawler.document_organizer.get_related_documents(doc_id)
        assert len(related) > 0  # Should find related documents


@pytest.mark.asyncio
async def test_search_functionality(
    integrated_crawler: DocumentationCrawler,
    test_html_dir: str
):
    """Test search functionality after crawling."""
    # Crawl all pages
    target = CrawlTarget(
        url=f"file://{test_html_dir}/index.html",
        depth=2,
        max_pages=10
    )
    
    await integrated_crawler.crawl(target)
    
    # Search for API documentation
    api_results = integrated_crawler.document_organizer.search(
        "api endpoint",
        category="api"
    )
    assert len(api_results) > 0
    
    # Search for Python examples
    example_results = integrated_crawler.document_organizer.search(
        "python example",
        category="example"
    )
    assert len(example_results) > 0
    
    # Search across all categories
    guide_results = integrated_crawler.document_organizer.search("getting started")
    assert len(guide_results) > 0


@pytest.mark.asyncio
async def test_error_handling_and_recovery(
    integrated_crawler: DocumentationCrawler,
    test_html_dir: str
):
    """Test error handling and recovery during crawling."""
    # Create a target with some invalid URLs
    target = CrawlTarget(
        url=f"file://{test_html_dir}/index.html",
        depth=2,
        max_pages=10,
        required_patterns=[".html", ".invalid"]  # Include invalid pattern
    )
    
    result = await integrated_crawler.crawl(target)
    
    # Should have some successful crawls despite errors
    assert result.stats.successful_crawls > 0
    assert result.stats.failed_crawls >= 0
    
    # Should have completed without raising exceptions
    assert result.stats.end_time is not None
    
    # Check error handling in quality metrics
    assert len(result.issues) >= 0  # May have quality issues
    assert all(hasattr(issue, 'severity') for issue in result.issues)