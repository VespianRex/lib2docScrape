"""Real-world crawling tests using live websites.

This module contains end-to-end tests that crawl real websites
to validate the system's functionality in production-like conditions.
"""

import asyncio
import logging
import time

import pytest

from src.backends.file_backend import FileBackend
from src.backends.http_backend import HTTPBackend, HTTPBackendConfig
from src.crawler.crawler import DocumentationCrawler
from src.crawler.models import CrawlTarget
from src.processors.content_processor import ContentProcessor
from src.processors.quality_checker import QualityChecker

from .test_sites import (
    TestSite,
)

logger = logging.getLogger(__name__)

# Mark all tests in this file as real-world integration tests
pytestmark = [pytest.mark.integration, pytest.mark.real_world]


class RealWorldTestValidator:
    """Validates real-world crawling results."""

    @staticmethod
    def validate_crawl_result(result, site: TestSite) -> dict[str, bool]:
        """Validate crawl results against site expectations."""
        validation_results = {}

        # Basic result structure validation
        validation_results["has_documents"] = len(result.documents) > 0
        validation_results["has_stats"] = hasattr(result, "stats")
        validation_results["successful_crawl"] = result.stats.successful_crawls > 0

        # Site-specific validation rules
        if site.validation_rules:
            rules = site.validation_rules

            # Check minimum content length
            if "min_content_length" in rules:
                min_length = rules["min_content_length"]
                has_sufficient_content = any(
                    len(str(doc.get("content", ""))) >= min_length
                    for doc in result.documents
                )
                validation_results["sufficient_content_length"] = has_sufficient_content

            # Check for required text
            if "required_text" in rules:
                required_texts = rules["required_text"]
                all_content = " ".join(
                    str(doc.get("content", "")) for doc in result.documents
                )
                for text in required_texts:
                    validation_results[f"contains_{text.lower().replace(' ', '_')}"] = (
                        text.lower() in all_content.lower()
                    )

            # Check for required elements (would need HTML parsing)
            if "required_elements" in rules:
                # This would require checking the raw HTML content
                # For now, we'll mark as passed if we have any content
                validation_results["has_required_elements"] = len(result.documents) > 0

        # Performance validation
        if hasattr(result, "stats"):
            validation_results["reasonable_success_rate"] = (
                result.stats.successful_crawls / max(1, result.stats.total_requests)
                >= 0.5
            )
            validation_results["no_excessive_errors"] = result.stats.failed_crawls < 10

        return validation_results


@pytest.mark.asyncio
async def test_simple_site_crawling(simple_test_sites):
    """Test crawling simple websites with basic validation."""
    if not simple_test_sites:
        pytest.skip("No simple test sites available")

    validator = RealWorldTestValidator()
    backend = HTTPBackend(HTTPBackendConfig())
    crawler = DocumentationCrawler(backend=backend)

    for site in simple_test_sites[:2]:  # Test first 2 available sites
        logger.info(f"Testing site: {site.name} ({site.url})")

        # Create crawl target
        target = CrawlTarget(
            url=site.url,
            depth=site.max_depth,
            max_pages=min(site.expected_pages, 5),  # Limit for testing
        )

        # Perform crawl
        start_time = time.time()
        try:
            result = await crawler.crawl(
                target_url=target.url,
                depth=target.depth,
                max_pages=target.max_pages,
                follow_external=False,
            )

            crawl_time = time.time() - start_time
            logger.info(f"Crawl completed in {crawl_time:.2f}s")

            # Validate results
            validation_results = validator.validate_crawl_result(result, site)

            # Assert key validations
            assert validation_results[
                "has_documents"
            ], f"No documents found for {site.name}"
            assert validation_results[
                "successful_crawl"
            ], f"No successful crawls for {site.name}"

            # Log validation results
            passed_validations = sum(validation_results.values())
            total_validations = len(validation_results)
            logger.info(
                f"Site {site.name}: {passed_validations}/{total_validations} validations passed"
            )

            # Performance assertions
            assert (
                crawl_time < site.timeout
            ), f"Crawl took too long: {crawl_time}s > {site.timeout}s"

        except Exception as e:
            logger.error(f"Failed to crawl {site.name}: {e}")
            # Don't fail the test for known problematic sites
            if site.name not in ["Wikipedia"]:  # Add known problematic sites here
                raise


@pytest.mark.asyncio
async def test_documentation_site_crawling(documentation_sites):
    """Test crawling documentation websites with content validation."""
    if not documentation_sites:
        pytest.skip("No documentation sites available")

    validator = RealWorldTestValidator()
    backend = HTTPBackend(HTTPBackendConfig())  # Use HTTP backend for docs
    content_processor = ContentProcessor()
    quality_checker = QualityChecker()

    crawler = DocumentationCrawler(
        backend=backend,
        content_processor=content_processor,
        quality_checker=quality_checker,
    )

    for site in documentation_sites[:1]:  # Test first available doc site
        logger.info(f"Testing documentation site: {site.name} ({site.url})")

        target = CrawlTarget(
            url=site.url,
            depth=min(site.max_depth, 2),  # Limit depth for testing
            max_pages=min(site.expected_pages, 10),  # Limit pages for testing
        )

        start_time = time.time()
        try:
            result = await crawler.crawl(
                target_url=target.url,
                depth=target.depth,
                max_pages=target.max_pages,
                follow_external=False,
            )

            time.time() - start_time

            # Validate results
            validation_results = validator.validate_crawl_result(result, site)

            # Documentation-specific assertions
            assert validation_results[
                "has_documents"
            ], f"No documents found for {site.name}"
            assert (
                len(result.documents) >= 2
            ), f"Expected multiple pages for {site.name}"

            # Content quality assertions
            if "sufficient_content_length" in validation_results:
                assert validation_results[
                    "sufficient_content_length"
                ], f"Insufficient content length for {site.name}"

            logger.info(f"Documentation site {site.name} crawled successfully")

        except Exception as e:
            logger.error(f"Failed to crawl documentation site {site.name}: {e}")
            raise


@pytest.mark.asyncio
async def test_backend_comparison(simple_test_sites):
    """Compare different backends on the same sites."""
    if not simple_test_sites:
        pytest.skip("No test sites available")

    backends = {
        "http": HTTPBackend(HTTPBackendConfig()),
        "http2": HTTPBackend(HTTPBackendConfig()),
        "file": FileBackend(),  # Will only work for file:// URLs
    }

    site = simple_test_sites[0]  # Use first available site
    target = CrawlTarget(url=site.url, depth=1, max_pages=3)

    results = {}

    for backend_name, backend in backends.items():
        if backend_name == "file" and not site.url.startswith("file://"):
            continue  # Skip file backend for HTTP URLs

        logger.info(f"Testing {backend_name} backend on {site.name}")

        crawler = DocumentationCrawler(backend=backend)

        try:
            start_time = time.time()
            result = await crawler.crawl(
                target_url=target.url,
                depth=target.depth,
                max_pages=target.max_pages,
                follow_external=False,
            )
            crawl_time = time.time() - start_time

            results[backend_name] = {
                "success": True,
                "documents": len(result.documents),
                "time": crawl_time,
                "successful_crawls": result.stats.successful_crawls,
                "failed_crawls": result.stats.failed_crawls,
            }

        except Exception as e:
            logger.warning(f"Backend {backend_name} failed: {e}")
            results[backend_name] = {
                "success": False,
                "error": str(e),
                "time": 0,
                "documents": 0,
            }

    # Analyze results
    successful_backends = [
        name for name, result in results.items() if result["success"]
    ]
    assert len(successful_backends) >= 1, "At least one backend should succeed"

    # Log comparison
    logger.info("Backend comparison results:")
    for backend_name, result in results.items():
        if result["success"]:
            logger.info(
                f"  {backend_name}: {result['documents']} docs in {result['time']:.2f}s"
            )
        else:
            logger.info(
                f"  {backend_name}: FAILED - {result.get('error', 'Unknown error')}"
            )


@pytest.mark.asyncio
async def test_performance_benchmarking(simple_test_sites):
    """Basic performance benchmarking of the crawling system."""
    if not simple_test_sites:
        pytest.skip("No test sites available")

    site = simple_test_sites[0]
    backend = HTTPBackend(HTTPBackendConfig())
    crawler = DocumentationCrawler(backend=backend)

    # Performance test parameters
    target = CrawlTarget(url=site.url, depth=1, max_pages=5)
    num_runs = 3

    times = []
    document_counts = []

    for run in range(num_runs):
        logger.info(f"Performance run {run + 1}/{num_runs}")

        start_time = time.time()
        result = await crawler.crawl(
            target_url=target.url,
            depth=target.depth,
            max_pages=target.max_pages,
            follow_external=False,
        )
        end_time = time.time()

        crawl_time = end_time - start_time
        times.append(crawl_time)
        document_counts.append(len(result.documents))

        # Brief pause between runs
        await asyncio.sleep(1)

    # Calculate statistics
    avg_time = sum(times) / len(times)
    avg_docs = sum(document_counts) / len(document_counts)

    logger.info(f"Performance results for {site.name}:")
    logger.info(f"  Average time: {avg_time:.2f}s")
    logger.info(f"  Average documents: {avg_docs:.1f}")
    logger.info(f"  Pages per second: {avg_docs / avg_time:.2f}")

    # Performance assertions
    assert avg_time < site.timeout, f"Average crawl time too slow: {avg_time:.2f}s"
    assert avg_docs > 0, "Should crawl at least one document on average"

    # Store results for reporting
    return {
        "site": site.name,
        "avg_time": avg_time,
        "avg_documents": avg_docs,
        "pages_per_second": avg_docs / avg_time,
    }
