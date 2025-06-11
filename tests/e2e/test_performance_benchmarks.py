"""Performance benchmarking tests for real-world scenarios.

This module provides comprehensive performance testing including:
- Throughput benchmarks
- Memory usage monitoring
- Concurrent crawling tests
- Backend performance comparison
"""

import asyncio
import logging
import statistics
import time
from dataclasses import dataclass

import psutil
import pytest

from src.backends.http_backend import HTTPBackend, HTTPBackendConfig  # type: ignore
from src.crawler.crawler import DocumentationCrawler  # type: ignore
from src.crawler.models import CrawlTarget  # type: ignore

from .test_sites import TestSite  # type: ignore

logger = logging.getLogger(__name__)

# Mark all tests as performance benchmarks
pytestmark = [pytest.mark.performance, pytest.mark.real_world]


@dataclass
class PerformanceMetrics:
    """Container for performance metrics."""

    duration: float
    documents_crawled: int
    pages_per_second: float
    memory_usage_mb: float
    cpu_usage_percent: float
    successful_requests: int
    failed_requests: int
    success_rate: float


class PerformanceMonitor:
    """Monitors system performance during crawling."""

    def __init__(self):
        self.process = psutil.Process()
        self.start_memory: float = 0.0
        self.start_cpu_time: float = 0.0
        self.start_time: float = 0.0

    def start_monitoring(self):
        """Start performance monitoring."""
        # Get current process
        proc: psutil.Process = self.process

        # Get memory info
        memory_info = proc.memory_info()  # type: ignore
        self.start_memory = memory_info.rss / 1024 / 1024  # MB

        # Get CPU times
        cpu_times = proc.cpu_times()  # type: ignore
        self.start_cpu_time = cpu_times.user + cpu_times.system

        self.start_time = time.time()

    def get_metrics(
        self, documents_crawled: int, successful_requests: int, failed_requests: int
    ) -> PerformanceMetrics:
        """Get current performance metrics."""
        end_time = time.time()

        # Get current process
        proc: psutil.Process = self.process

        # Get memory info
        memory_info = proc.memory_info()  # type: ignore
        end_memory = memory_info.rss / 1024 / 1024  # MB

        # Get CPU times
        cpu_times = proc.cpu_times()  # type: ignore
        end_cpu_time = cpu_times.user + cpu_times.system

        duration = end_time - self.start_time
        memory_usage = end_memory - self.start_memory
        # Ensure duration is not zero to avoid DivisionByZeroError
        cpu_usage = ((end_cpu_time - self.start_cpu_time) / max(duration, 0.001)) * 100

        total_requests = successful_requests + failed_requests
        success_rate = successful_requests / max(1, total_requests)
        pages_per_second = documents_crawled / max(0.001, duration)

        return PerformanceMetrics(
            duration=duration,
            documents_crawled=documents_crawled,
            pages_per_second=pages_per_second,
            memory_usage_mb=memory_usage,
            cpu_usage_percent=cpu_usage,
            successful_requests=successful_requests,
            failed_requests=failed_requests,
            success_rate=success_rate,
        )


@pytest.mark.asyncio
async def test_single_site_performance(simple_test_sites):
    """Benchmark performance on a single site."""
    if not simple_test_sites:
        pytest.skip("No test sites available")

    current_site = simple_test_sites[0]  # Renamed variable
    backend = HTTPBackend(HTTPBackendConfig())
    crawler = DocumentationCrawler(backend=backend)
    monitor = PerformanceMonitor()

    target = CrawlTarget(
        url=current_site.url,  # Use renamed variable
        depth=2,
        max_pages=10,
    )

    logger.info(
        f"Starting performance benchmark for {current_site.name}"
    )  # Use renamed variable
    monitor.start_monitoring()

    result = await crawler.crawl(
        target_url=target.url,
        depth=target.depth,
        max_pages=target.max_pages,
        follow_external=False,
    )

    metrics = monitor.get_metrics(
        documents_crawled=len(result.documents),
        successful_requests=result.stats.successful_crawls,
        failed_requests=result.stats.failed_crawls,
    )

    # Log performance results
    logger.info(
        f"Performance benchmark results for {current_site.name}:"
    )  # Use renamed variable
    logger.info(f"  Duration: {metrics.duration:.2f}s")
    logger.info(f"  Documents: {metrics.documents_crawled}")
    logger.info(f"  Pages/sec: {metrics.pages_per_second:.2f}")
    logger.info(f"  Memory usage: {metrics.memory_usage_mb:.1f} MB")
    logger.info(f"  CPU usage: {metrics.cpu_usage_percent:.1f}%")
    logger.info(f"  Success rate: {metrics.success_rate:.1%}")

    # Performance assertions
    assert metrics.pages_per_second > 0.1, "Should crawl at least 0.1 pages per second"
    assert metrics.success_rate > 0.5, "Should have >50% success rate"
    assert metrics.memory_usage_mb < 500, "Should use less than 500MB additional memory"

    return metrics


@pytest.mark.asyncio
async def test_backend_performance_comparison(simple_test_sites):
    """Compare performance of different backends."""
    if not simple_test_sites:
        pytest.skip("No test sites available")

    current_site = simple_test_sites[0]  # Renamed variable
    backends = {
        "http": HTTPBackend(HTTPBackendConfig()),
        # "http2": HTTPBackend(HTTPBackendConfig()) # Example if another backend type/config was used
    }

    target = CrawlTarget(
        url=current_site.url, depth=1, max_pages=5
    )  # Use renamed variable
    results = {}

    for backend_name, backend in backends.items():
        logger.info(f"Benchmarking {backend_name} backend")

        crawler = DocumentationCrawler(backend=backend)
        monitor = PerformanceMonitor()

        try:
            monitor.start_monitoring()

            result = await crawler.crawl(
                target_url=target.url,
                depth=target.depth,
                max_pages=target.max_pages,
                follow_external=False,
            )

            metrics = monitor.get_metrics(
                documents_crawled=len(result.documents),
                successful_requests=result.stats.successful_crawls,
                failed_requests=result.stats.failed_crawls,
            )

            results[backend_name] = metrics

        except Exception as e:
            logger.warning(f"Backend {backend_name} failed: {e}")
            continue

    # Compare results
    if results:  # Check if there are any results
        backend_names = list(results.keys())
        if len(results) >= 2:
            backend1, backend2 = backend_names[0], backend_names[1]
            metrics1, metrics2 = results[backend1], results[backend2]

            logger.info("Backend performance comparison:")
            logger.info(
                f"  {backend1}: {metrics1.pages_per_second:.2f} pages/sec, Success: {metrics1.success_rate:.1%}"
            )
            logger.info(
                f"  {backend2}: {metrics2.pages_per_second:.2f} pages/sec, Success: {metrics2.success_rate:.1%}"
            )
            assert metrics2.success_rate > 0.3, f"{backend2} success rate too low"
        elif len(results) == 1:  # Log info for single backend case
            backend1 = backend_names[0]
            metrics1 = results[backend1]
            logger.info(
                f"Performance for {backend1}: {metrics1.pages_per_second:.2f} pages/sec, Success: {metrics1.success_rate:.1%}"
            )

        # Common assertion for all tested backends
        for backend_name_key in results:  # Renamed loop variable
            assert (
                results[backend_name_key].success_rate > 0.3
            ), f"{backend_name_key} success rate too low"

    return results


@pytest.mark.asyncio
async def test_concurrent_crawling_performance(simple_test_sites):
    """Test performance with concurrent crawling."""
    if len(simple_test_sites) < 2:
        pytest.skip("Need at least 2 test sites for concurrent testing")

    backend = HTTPBackend(HTTPBackendConfig())
    sites_to_crawl = simple_test_sites[:3]  # Use up to 3 sites, renamed variable

    async def crawl_site_concurrently(
        site_to_crawl: TestSite,
    ) -> PerformanceMetrics:  # Renamed function and parameter
        """Crawl a single site and return metrics."""
        # Each task needs its own crawler and monitor instance for true concurrency simulation
        local_crawler = DocumentationCrawler(backend=backend)
        local_monitor = PerformanceMonitor()

        target = CrawlTarget(url=site_to_crawl.url, depth=1, max_pages=3)

        local_monitor.start_monitoring()
        crawl_result = await local_crawler.crawl(  # Renamed variable
            target_url=target.url,
            depth=target.depth,
            max_pages=target.max_pages,
            follow_external=False,
        )

        return local_monitor.get_metrics(
            documents_crawled=len(crawl_result.documents),  # Use renamed variable
            successful_requests=crawl_result.stats.successful_crawls,  # Use renamed variable
            failed_requests=crawl_result.stats.failed_crawls,  # Use renamed variable
        )

    logger.info(
        f"Starting concurrent crawling of {len(sites_to_crawl)} sites"
    )  # Use renamed variable
    overall_start_time = time.time()  # Renamed variable

    # Run concurrent crawls
    tasks = [
        crawl_site_concurrently(s) for s in sites_to_crawl
    ]  # Use renamed function and variable
    gathered_results = await asyncio.gather(
        *tasks, return_exceptions=True
    )  # Renamed variable

    total_time_taken = time.time() - overall_start_time  # Renamed variable

    # Process results
    successful_results = [
        r for r in gathered_results if isinstance(r, PerformanceMetrics)
    ]  # Use renamed variable
    failed_crawl_results = [
        r for r in gathered_results if isinstance(r, Exception)
    ]  # Use renamed variable

    logger.info(
        f"Concurrent crawling completed in {total_time_taken:.2f}s"
    )  # Use renamed variable
    logger.info(
        f"  Successful: {len(successful_results)}/{len(sites_to_crawl)}"
    )  # Use renamed variable
    logger.info(f"  Failed: {len(failed_crawl_results)}")  # Use renamed variable

    if successful_results:
        total_documents = sum(r.documents_crawled for r in successful_results)
        # Ensure total_time_taken is not zero
        avg_pages_per_sec = total_documents / max(
            total_time_taken, 0.001
        )  # Use renamed variable

        logger.info(f"  Total documents: {total_documents}")
        logger.info(f"  Overall pages/sec: {avg_pages_per_sec:.2f}")

        # Concurrent performance should be reasonable
        assert (
            len(successful_results) >= len(sites_to_crawl) // 2
        ), "At least half should succeed"  # Use renamed variable
        assert avg_pages_per_sec > 0.1, "Should maintain reasonable throughput"

    return {
        "total_time": total_time_taken,  # Use renamed variable
        "successful_crawls": len(successful_results),
        "failed_crawls": len(failed_crawl_results),  # Use renamed variable
        "results": successful_results,
    }


@pytest.mark.asyncio
async def test_memory_usage_stability(simple_test_sites):
    """Test memory usage stability over multiple crawls."""
    if not simple_test_sites:
        pytest.skip("No test sites available")

    site_for_memory_test = simple_test_sites[0]  # Renamed variable
    backend = HTTPBackend(HTTPBackendConfig())

    memory_measurements = []
    num_iterations = 5

    for i in range(num_iterations):
        logger.info(f"Memory stability test iteration {i + 1}/{num_iterations}")

        # Measure memory before crawl
        process: psutil.Process = psutil.Process()
        memory_before = process.memory_info().rss / 1024 / 1024  # MB  # type: ignore

        # Perform crawl
        crawler = DocumentationCrawler(backend=backend)
        target = CrawlTarget(
            url=site_for_memory_test.url, depth=1, max_pages=3
        )  # Use renamed variable

        await crawler.crawl(
            target_url=target.url,
            depth=target.depth,
            max_pages=target.max_pages,
            follow_external=False,
        )

        # Measure memory after crawl
        memory_after = process.memory_info().rss / 1024 / 1024  # MB  # type: ignore
        memory_diff = memory_after - memory_before

        memory_measurements.append(memory_diff)

        # Brief pause between iterations
        await asyncio.sleep(1)

    # Analyze memory usage
    avg_memory_usage = (
        statistics.mean(memory_measurements) if memory_measurements else 0.0
    )
    max_memory_usage = max(memory_measurements) if memory_measurements else 0.0
    memory_std = (
        statistics.stdev(memory_measurements) if len(memory_measurements) > 1 else 0.0
    )

    logger.info("Memory usage analysis:")  # Removed f-string as it had no placeholders
    logger.info(f"  Average per crawl: {avg_memory_usage:.1f} MB")
    logger.info(f"  Maximum per crawl: {max_memory_usage:.1f} MB")
    logger.info(f"  Standard deviation: {memory_std:.1f} MB")

    # Memory usage assertions
    assert avg_memory_usage < 100, "Average memory usage should be reasonable"
    assert max_memory_usage < 200, "Maximum memory usage should not be excessive"
    assert memory_std < 50, "Memory usage should be relatively stable"

    return {
        "measurements": memory_measurements,
        "average": avg_memory_usage,
        "maximum": max_memory_usage,
        "std_deviation": memory_std,
    }


@pytest.mark.asyncio
async def test_throughput_scaling(simple_test_sites):
    """Test how throughput scales with different page limits."""
    if not simple_test_sites:
        pytest.skip("No test sites available")

    site_for_scaling_test = simple_test_sites[0]  # Renamed variable
    backend = HTTPBackend(HTTPBackendConfig())

    page_limits = [1, 3, 5, 10]
    throughput_results = []

    for max_pages_limit in page_limits:  # Renamed loop variable
        logger.info(
            f"Testing throughput with max_pages={max_pages_limit}"
        )  # Use renamed variable

        crawler = DocumentationCrawler(backend=backend)
        target = CrawlTarget(
            url=site_for_scaling_test.url, depth=2, max_pages=max_pages_limit
        )  # Use renamed variables

        iter_start_time = time.time()  # Renamed variable
        crawl_iter_result = await crawler.crawl(  # Renamed variable
            target_url=target.url,
            depth=target.depth,
            max_pages=target.max_pages,
            follow_external=False,
        )
        iter_duration = time.time() - iter_start_time  # Renamed variable

        pages_per_second = len(crawl_iter_result.documents) / max(
            0.001, iter_duration
        )  # Use renamed variables

        throughput_results.append(
            {
                "max_pages": max_pages_limit,  # Use renamed variable
                "actual_pages": len(
                    crawl_iter_result.documents
                ),  # Use renamed variable
                "duration": iter_duration,  # Use renamed variable
                "pages_per_second": pages_per_second,
            }
        )

        logger.info(
            f"  Crawled {len(crawl_iter_result.documents)} pages in {iter_duration:.2f}s ({pages_per_second:.2f} pages/sec)"
        )  # Use renamed variables

    # Analyze scaling
    logger.info("Throughput scaling analysis:")
    for t_result in throughput_results:  # Renamed loop variable
        logger.info(
            f"  {t_result['max_pages']} pages limit: {t_result['pages_per_second']:.2f} pages/sec"
        )

    # Throughput should generally increase with more pages (up to a point)
    assert all(
        r_item["pages_per_second"] > 0 for r_item in throughput_results
    ), "All tests should have positive throughput"

    return throughput_results
