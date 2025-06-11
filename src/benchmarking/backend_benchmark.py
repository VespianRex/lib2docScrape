"""
Backend benchmarking module for comparing different crawler backends.
"""

import asyncio
import logging
import time
from datetime import datetime
from typing import Optional

import matplotlib.pyplot as plt
import pandas as pd
from pydantic import BaseModel, Field

from ..backends.base import CrawlerBackend
from ..backends.crawl4ai_backend import Crawl4AIBackend, Crawl4AIConfig
from ..backends.http_backend import HTTPBackend, HTTPBackendConfig
from ..backends.lightpanda_backend import LightpandaBackend, LightpandaConfig
from ..utils.url import URLInfo, create_url_info

logger = logging.getLogger(__name__)


class BenchmarkResult(BaseModel):
    """Model for storing benchmark results."""

    backend_name: str
    url: str
    success: bool
    status_code: int
    crawl_time: float
    content_size: int
    memory_usage: Optional[float] = None
    cpu_usage: Optional[float] = None
    error: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class BackendBenchmark:
    """
    Benchmark different crawler backends against the same URLs.
    Allows for concurrent execution and comparison of results.
    """

    def __init__(self):
        """Initialize the benchmark."""
        self.backends: dict[str, CrawlerBackend] = {}
        self.results: list[BenchmarkResult] = []

    def register_backend(self, backend: CrawlerBackend) -> None:
        """
        Register a backend for benchmarking.

        Args:
            backend: The backend to register
        """
        self.backends[backend.name] = backend
        logger.info(f"Registered backend: {backend.name}")

    def register_all_available_backends(self) -> None:
        """Register all available backends with default configurations."""
        # HTTP Backend
        http_backend = HTTPBackend(config=HTTPBackendConfig())
        self.register_backend(http_backend)

        # Crawl4AI Backend
        crawl4ai_backend = Crawl4AIBackend(config=Crawl4AIConfig())
        self.register_backend(crawl4ai_backend)

        # Lightpanda Backend
        try:
            lightpanda_backend = LightpandaBackend(config=LightpandaConfig())
            self.register_backend(lightpanda_backend)
        except Exception as e:
            logger.warning(f"Could not register Lightpanda backend: {e}")

    async def benchmark_url(self, url: str, config=None) -> dict[str, BenchmarkResult]:
        """
        Benchmark all registered backends against a single URL.

        Args:
            url: The URL to benchmark
            config: Optional crawler configuration

        Returns:
            Dictionary mapping backend names to benchmark results
        """
        url_info = create_url_info(url)
        if not url_info.is_valid:
            logger.error(f"Invalid URL for benchmarking: {url}")
            return {}

        results = {}
        tasks = []

        for name, backend in self.backends.items():
            task = asyncio.create_task(
                self._benchmark_single_backend(name, backend, url_info, config)
            )
            tasks.append(task)

        # Wait for all tasks to complete
        completed_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for i, (name, _) in enumerate(self.backends.items()):
            result = completed_results[i]
            if isinstance(result, Exception):
                logger.error(f"Error benchmarking {name} on {url}: {result}")
                results[name] = BenchmarkResult(
                    backend_name=name,
                    url=url,
                    success=False,
                    status_code=0,
                    crawl_time=0.0,
                    content_size=0,
                    error=str(result),
                )
            else:
                results[name] = result
                self.results.append(result)

        return results

    async def _benchmark_single_backend(
        self, name: str, backend: CrawlerBackend, url_info: URLInfo, config=None
    ) -> BenchmarkResult:
        """
        Benchmark a single backend against a URL.

        Args:
            name: Backend name
            backend: Backend instance
            url_info: URLInfo object
            config: Optional crawler configuration

        Returns:
            BenchmarkResult with performance metrics
        """
        start_time = time.time()

        try:
            # Measure memory before
            # In a real implementation, this would use psutil or similar
            memory_before = 0

            # Crawl the URL
            result = await backend.crawl(url_info, config)

            # Measure memory after
            # In a real implementation, this would use psutil or similar
            memory_after = 0

            # Calculate metrics
            end_time = time.time()
            crawl_time = end_time - start_time
            content_size = len(str(result.content.get("html", "")))
            memory_usage = memory_after - memory_before

            return BenchmarkResult(
                backend_name=name,
                url=str(url_info.normalized_url),
                success=result.is_success(),
                status_code=result.status,
                crawl_time=crawl_time,
                content_size=content_size,
                memory_usage=memory_usage,
                error=result.error,
            )

        except Exception as e:
            end_time = time.time()
            crawl_time = end_time - start_time

            return BenchmarkResult(
                backend_name=name,
                url=str(url_info.normalized_url),
                success=False,
                status_code=0,
                crawl_time=crawl_time,
                content_size=0,
                error=str(e),
            )

    async def benchmark_urls(
        self, urls: list[str], config=None
    ) -> dict[str, list[BenchmarkResult]]:
        """
        Benchmark all registered backends against multiple URLs.

        Args:
            urls: List of URLs to benchmark
            config: Optional crawler configuration

        Returns:
            Dictionary mapping backend names to lists of benchmark results
        """
        all_results: dict[str, list[BenchmarkResult]] = {
            name: [] for name in self.backends
        }

        for url in urls:
            url_results = await self.benchmark_url(url, config)
            for name, result in url_results.items():
                if name in all_results:
                    all_results[name].append(result)

        return all_results

    def generate_report(self, output_file: Optional[str] = None) -> str:
        """
        Generate a benchmark report.

        Args:
            output_file: Optional file path to save the report

        Returns:
            Report as a string
        """
        if not self.results:
            return "No benchmark results available."

        # Convert results to DataFrame for easier analysis
        data = []
        for result in self.results:
            data.append(
                {
                    "Backend": result.backend_name,
                    "URL": result.url,
                    "Success": result.success,
                    "Status Code": result.status_code,
                    "Crawl Time (s)": result.crawl_time,
                    "Content Size (bytes)": result.content_size,
                    "Memory Usage (MB)": result.memory_usage
                    if result.memory_usage
                    else 0,
                    "Error": result.error if result.error else "",
                }
            )

        df = pd.DataFrame(data)

        # Generate summary statistics
        summary = df.groupby("Backend").agg(
            {
                "Success": "mean",
                "Crawl Time (s)": ["mean", "min", "max", "std"],
                "Content Size (bytes)": ["mean", "min", "max"],
                "Memory Usage (MB)": "mean",
            }
        )

        # Format report
        report = "# Backend Benchmark Report\n\n"
        report += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        report += f"Total URLs: {len(df['URL'].unique())}\n"
        report += f"Total Backends: {len(df['Backend'].unique())}\n\n"

        report += "## Summary Statistics\n\n"
        report += summary.to_markdown()
        report += "\n\n"

        report += "## Success Rate\n\n"
        success_rate = (
            df.groupby("Backend")["Success"].mean().sort_values(ascending=False)
        )
        report += success_rate.to_markdown()
        report += "\n\n"

        # Save report if output file is specified
        if output_file:
            with open(output_file, "w") as f:
                f.write(report)

            # Generate charts
            self._generate_charts(df, output_file.replace(".md", ""))

        return report

    def _generate_charts(self, df: pd.DataFrame, base_filename: str) -> None:
        """
        Generate charts for the benchmark results.

        Args:
            df: DataFrame with benchmark results
            base_filename: Base filename for the charts
        """
        # Crawl Time Comparison
        plt.figure(figsize=(10, 6))
        crawl_time_data = df.groupby("Backend")["Crawl Time (s)"].mean().sort_values()
        crawl_time_data.plot(kind="bar")
        plt.title("Average Crawl Time by Backend")
        plt.ylabel("Time (seconds)")
        plt.tight_layout()
        plt.savefig(f"{base_filename}_crawl_time.png")

        # Success Rate Comparison
        plt.figure(figsize=(10, 6))
        success_rate = (
            df.groupby("Backend")["Success"].mean().sort_values(ascending=False)
        )
        success_rate.plot(kind="bar")
        plt.title("Success Rate by Backend")
        plt.ylabel("Success Rate")
        plt.ylim(0, 1)
        plt.tight_layout()
        plt.savefig(f"{base_filename}_success_rate.png")

        # Content Size Comparison
        plt.figure(figsize=(10, 6))
        content_size = (
            df.groupby("Backend")["Content Size (bytes)"].mean().sort_values()
        )
        content_size.plot(kind="bar")
        plt.title("Average Content Size by Backend")
        plt.ylabel("Size (bytes)")
        plt.tight_layout()
        plt.savefig(f"{base_filename}_content_size.png")

    async def close(self) -> None:
        """Close all backends."""
        for backend in self.backends.values():
            await backend.close()
