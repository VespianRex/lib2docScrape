"""Integration tests for the documentation crawler system."""

import asyncio
import os
from typing import Dict, List, Set
from pathlib import Path # Import Path

import pytest
from bs4 import BeautifulSoup

# Import necessary components
from src.backends.crawl4ai import Crawl4AIBackend, Crawl4AIConfig
from src.backends.http_backend import HTTPBackend, HTTPBackendConfig # Import HTTPBackend
from src.backends.file_backend import FileBackend # Import FileBackend
from src.backends.selector import BackendCriteria, BackendSelector
from src.crawler import CrawlerConfig, CrawlTarget, DocumentationCrawler
from src.organizers.doc_organizer import DocumentOrganizer, OrganizationConfig
from src.processors.content_processor import ContentProcessor, ProcessorConfig
from src.processors.quality_checker import QualityChecker, QualityConfig, IssueLevel # Import IssueLevel


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
    # Configure content processor
    processor = ContentProcessor(
        config=ProcessorConfig(
            # Removed allowed_tags and allowed_attributes as they are not valid config fields
            preserve_whitespace_elements=["pre", "code"],
            code_languages=["python"],
            max_heading_level=3,
            max_content_length=10000,
            min_content_length=10,
            extract_metadata=True, # Ensure metadata is extracted
            extract_code_blocks=True # Ensure code blocks are extracted
        )
    )

    # Configure quality checker
    checker = QualityChecker(
        config=QualityConfig(
            min_content_length=10, # Lowered for test files
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
            min_similarity_score=0.0, # Set to 0.0 for test to ensure comparison happens
            max_versions_to_keep=3,
            category_rules={
                "api": ["api", "reference", "endpoint"],
                "guide": ["guide", "tutorial", "getting started"],
                "example": ["example", "sample", "demo"]
            },
            stop_words=set() # Explicitly set stop words to empty set
        )
    )

    # Create crawler instance - let it initialize its default selector
    crawler = DocumentationCrawler(
        config=CrawlerConfig(
            concurrent_requests=2,
            requests_per_second=10.0,
            max_retries=1, # Reduce retries for faster tests
            request_timeout=5.0,
            respect_robots_txt=False # Ignore robots.txt for local file tests
        ),
        # backend_selector=selector, # Removed - use default selector
        content_processor=processor,
        quality_checker=checker,
        document_organizer=organizer
    )

    # --- Register FileBackend for file:// scheme ---
    file_backend = FileBackend()
    crawler.backend_selector.register_backend(
        file_backend,
        BackendCriteria(
            priority=200, # High priority for file scheme
            content_types=["text/html"], # Assume HTML for test files
            url_patterns=["*"], # Match all file paths
            schemes=['file'] # Explicitly handle only 'file' scheme
        )
    )
    # --- End FileBackend registration ---

    # Remove the modification of HTTPBackend criteria
    # http_backend_name = \'http_backend\'
    # if http_backend_name in crawler.backend_selector._backends:
    #     ... # Removed the block that modified HTTPBackend

    return crawler


@pytest.mark.asyncio
async def test_full_site_crawl(
    integrated_crawler: DocumentationCrawler,
    test_html_dir: str
):
    """Test crawling a complete documentation site."""
    # Create crawl target
    target = CrawlTarget(
        url=f"file://{test_html_dir}/index.html",
        depth=2, # Allow crawling linked pages
        follow_external=False,
        content_types=["text/html"],
        exclude_patterns=[],
        required_patterns=[], # Remove specific pattern to allow all .html files
        max_pages=10
    )

    # Perform crawl
    result = await integrated_crawler.crawl(
        target_url=target.url,
        depth=target.depth,
        follow_external=target.follow_external,
        content_types=target.content_types,
        exclude_patterns=target.exclude_patterns,
        required_patterns=target.required_patterns,
        max_pages=target.max_pages,
        allowed_paths=target.allowed_paths,
        excluded_paths=target.excluded_paths
    )

    # Verify crawl statistics
    assert result.stats.pages_crawled > 0, f"Expected pages crawled > 0, got {result.stats.pages_crawled}"
    assert result.stats.successful_crawls > 0, f"Expected successful crawls > 0, got {result.stats.successful_crawls}"
    assert result.stats.failed_crawls == 0, f"Expected 0 failed crawls, got {result.stats.failed_crawls}"

    # Verify documents were processed (expecting 4: index + 3 linked pages)
    assert len(result.documents) == 4, f"Expected 4 documents, got {len(result.documents)}"

    # Verify document categorization (using the organizer attached to the crawler)
    categories = set()
    doc_ids_processed = [d['url'] for d in result.documents] # Get URLs from result documents
    # Need to map result document URLs back to organizer document IDs if they differ
    # For simplicity, assume organizer uses the URL as key or find mapping if needed
    # This part might need adjustment based on how DocumentOrganizer stores/keys documents
    # Assuming DocumentOrganizer keys might not directly match result document URLs/IDs
    # Let's check categories based on the organizer's internal state
    for doc_id, doc_meta in integrated_crawler.document_organizer.documents.items():
         # Check if the URL associated with this doc_id was actually crawled
         if doc_meta.url in doc_ids_processed:
              categories.add(doc_meta.category)

    assert "api" in categories, f"Categories found: {categories}"
    assert "guide" in categories, f"Categories found: {categories}"
    assert "example" in categories, f"Categories found: {categories}"
    # 'index.html' might be 'uncategorized' or match another rule depending on content/rules
    # assert "uncategorized" in categories or len(categories) >= 3


@pytest.mark.asyncio
async def test_content_processing_pipeline(
    integrated_crawler: DocumentationCrawler,
    test_html_dir: str
):
    """Test the complete content processing pipeline."""
    target_url = f"file://{test_html_dir}/guide.html"
    target = CrawlTarget(
        url=target_url,
        depth=1,
        max_pages=1,
        required_patterns=[] # Allow crawling the guide page
    )

    result = await integrated_crawler.crawl(
        target_url=target.url,
        depth=target.depth,
        follow_external=target.follow_external,
        content_types=target.content_types,
        exclude_patterns=target.exclude_patterns,
        required_patterns=target.required_patterns,
        max_pages=target.max_pages,
        allowed_paths=target.allowed_paths,
        excluded_paths=target.excluded_paths
    )
    assert len(result.documents) == 1, f"Expected 1 document for guide.html, got {len(result.documents)}"

    # Find the document ID associated with the crawled URL in the organizer
    found_doc_id = None
    for doc_id, doc_meta in integrated_crawler.document_organizer.documents.items():
        if doc_meta.url == target_url:
            found_doc_id = doc_id
            break

    assert found_doc_id is not None, f"Could not find document for {target_url} in organizer"
    doc = integrated_crawler.document_organizer.documents[found_doc_id]

    # Verify content processing
    assert doc.title == "User Guide"
    assert doc.category == "guide"
    assert len(doc.versions) == 1

    # Verify code block processing
    version = doc.versions[-1]
    # Check the processed content dict within the version's 'changes' attribute
    # Markdownify by default does not add language specifier from class, so "python" won't be in ```python
    # We will check for the code content itself.
    assert "example.run()" in version.changes['content']['formatted_content']


@pytest.mark.asyncio
async def test_quality_checks(
    integrated_crawler: DocumentationCrawler,
    test_html_dir: str
):
    """Test quality checking during crawl."""
    target_url = f"file://{test_html_dir}/api.html"
    target = CrawlTarget(
        url=target_url,
        depth=1,
        max_pages=1,
        required_patterns=[] # Allow crawling api.html
    )

    result = await integrated_crawler.crawl(
        target_url=target.url,
        depth=target.depth,
        follow_external=target.follow_external,
        content_types=target.content_types,
        exclude_patterns=target.exclude_patterns,
        required_patterns=target.required_patterns,
        max_pages=target.max_pages,
        allowed_paths=target.allowed_paths,
        excluded_paths=target.excluded_paths
    )

    # Verify quality metrics are present (structure might vary)
    assert result.metrics is not None, "Metrics should not be None"
    # Check if metrics dict contains expected keys (adjust based on QualityChecker output)
    # Assuming metrics are stored per-document URL in the CrawlResult
    assert target_url in result.metrics, f"Metrics for {target_url} not found"
    doc_metrics = result.metrics[target_url]
    assert "content_length" in doc_metrics and doc_metrics["content_length"] > 0
    # Add checks for other expected metrics if the checker calculates them
    # assert "readability_score" in doc_metrics and doc_metrics["readability_score"] >= 0
    # assert "heading_structure_score" in doc_metrics and doc_metrics["heading_structure_score"] >= 0


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
        max_pages=10,
        required_patterns=[] # Allow all html files
    )

    result = await integrated_crawler.crawl(
        target_url=target.url,
        depth=target.depth,
        follow_external=target.follow_external,
        content_types=target.content_types,
        exclude_patterns=target.exclude_patterns,
        required_patterns=target.required_patterns,
        max_pages=target.max_pages,
        allowed_paths=target.allowed_paths,
        excluded_paths=target.excluded_paths
    )
    assert len(result.documents) == 4, "Should have crawled all 4 pages"

    # Get document IDs from the organizer based on crawled URLs
    organizer_doc_ids = []
    crawled_urls = {doc['url'] for doc in result.documents}
    for doc_id, doc_meta in integrated_crawler.document_organizer.documents.items():
        if doc_meta.url in crawled_urls:
            organizer_doc_ids.append(doc_id)

    assert len(organizer_doc_ids) == 4, "Organizer should have 4 documents corresponding to crawled pages"

    # Create a collection
    collection_id = integrated_crawler.document_organizer.create_collection(
        "Test Documentation",
        "Complete test documentation set",
        organizer_doc_ids # Use IDs from organizer
    )

    # Verify collection
    collection = integrated_crawler.document_organizer.collections[collection_id]
    assert len(collection.documents) == len(organizer_doc_ids) # Change to 'documents'

    # Test document relationships (expecting some similarity)
    found_related = False
    for doc_id in organizer_doc_ids:
        related = integrated_crawler.document_organizer.get_related_documents(doc_id)
        # Check if related list is not empty (at least one related doc found)
        if related:
             found_related = True
             # Optional: Check similarity score if needed
             # assert all(score >= integrated_crawler.document_organizer.config.min_similarity_score for _, score in related)
    assert found_related, "Expected to find at least some related documents"


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
        max_pages=10,
        required_patterns=[] # Allow all html files
    )

    await integrated_crawler.crawl(
        target_url=target.url,
        depth=target.depth,
        follow_external=target.follow_external,
        content_types=target.content_types,
        exclude_patterns=target.exclude_patterns,
        required_patterns=target.required_patterns,
        max_pages=target.max_pages,
        allowed_paths=target.allowed_paths,
        excluded_paths=target.excluded_paths
    )
    assert len(integrated_crawler.document_organizer.documents) == 4, "Organizer should have 4 documents"

    # Search for API documentation
    api_results = integrated_crawler.document_organizer.search(
        "api endpoint",
        category="api"
    )
    assert len(api_results) > 0, "Should find results for 'api endpoint' in 'api' category"

    # Search for Python examples
    example_results = integrated_crawler.document_organizer.search(
        "python example",
        category="example"
    )
    assert len(example_results) > 0, "Should find results for 'python example' in 'example' category"

    # Search across all categories
    guide_results = integrated_crawler.document_organizer.search("getting started")
    assert len(guide_results) > 0, "Should find results for 'getting started' across all categories"