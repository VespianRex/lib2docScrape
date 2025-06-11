#!/usr/bin/env python3
"""
Test lib2docScrape by scraping documentation for all project dependencies.

This script uses our own project to scrape documentation for all the libraries
we depend on, providing both a comprehensive test and valuable documentation.
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Optional

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.backends.crawl4ai_backend import Crawl4AIBackend  # noqa: E402
from src.backends.http_backend import HTTPBackend  # noqa: E402
from src.crawler import CrawlTarget, DocumentationCrawler  # noqa: E402
from src.processors.content_processor import ContentProcessor  # noqa: E402
from src.processors.quality_checker import QualityChecker  # noqa: E402

logger = logging.getLogger(__name__)


class DependencyDocumentationTester:
    """Tests lib2docScrape by scraping documentation for project dependencies."""

    def __init__(self, config: dict):
        self.config = config
        self.results = {
            "start_time": datetime.now().isoformat(),
            "config": config,
            "dependencies": {},
            "crawl_results": {},
            "performance_metrics": {},
            "summary": {},
        }

        # Documentation URL patterns for common libraries
        self.doc_url_patterns = {
            "aiohttp": "https://docs.aiohttp.org/en/stable/",
            "requests": "https://requests.readthedocs.io/en/latest/",
            "beautifulsoup4": "https://www.crummy.com/software/BeautifulSoup/bs4/doc/",
            "scrapy": "https://docs.scrapy.org/en/latest/",
            "pydantic": "https://docs.pydantic.dev/latest/",
            "markdownify": "https://pypi.org/project/markdownify/",
            "bleach": "https://bleach.readthedocs.io/en/latest/",
            "tldextract": "https://github.com/john-kurkowski/tldextract",
            "certifi": "https://pypi.org/project/certifi/",
            "duckduckgo-search": "https://pypi.org/project/duckduckgo-search/",
            "pytest": "https://docs.pytest.org/en/stable/",
            "fastapi": "https://fastapi.tiangolo.com/",
            "httpx": "https://www.python-httpx.org/",
            "jinja2": "https://jinja.palletsprojects.com/",
            "scikit-learn": "https://scikit-learn.org/stable/",
            "nltk": "https://www.nltk.org/",
            "psutil": "https://psutil.readthedocs.io/en/latest/",
            "crawl4ai": "https://github.com/unclecode/crawl4ai",
            "playwright": "https://playwright.dev/python/",
            "uvloop": "https://github.com/MagicStack/uvloop",
            "coverage": "https://coverage.readthedocs.io/en/latest/",
            "ruff": "https://docs.astral.sh/ruff/",
        }

    def extract_dependencies_from_discovery(self) -> dict[str, list[str]]:
        """Extract dependencies using the dependency discovery tool."""
        try:
            # Import and use the dependency discovery tool
            from dependency_discovery import DependencyDiscovery

            discovery = DependencyDiscovery(".")

            # Discover from all sources
            config_deps = discovery.discover_from_config_files()
            import_deps = discovery.discover_from_imports(["src", "tests"])

            # Get all unique dependencies
            all_deps = discovery.get_all_dependencies()

            # Store results
            dependencies = {
                "config_files": config_deps,
                "imports": import_deps.get("all_external", []),
                "all_unique": list(all_deps),
            }

            self.results["dependencies"] = dependencies
            return dependencies

        except Exception as e:
            logger.error(f"Failed to discover dependencies: {e}")
            # Fallback to manual list
            return {
                "fallback": [
                    "requests",
                    "aiohttp",
                    "beautifulsoup4",
                    "pytest",
                    "fastapi",
                    "pydantic",
                    "markdownify",
                ]
            }

    def get_documentation_url(self, package_name: str) -> Optional[str]:
        """Get documentation URL for a package."""
        # Check our predefined patterns first
        if package_name in self.doc_url_patterns:
            return self.doc_url_patterns[package_name]

        # For packages not in our patterns, try common patterns
        common_patterns = [
            f"https://{package_name}.readthedocs.io/en/latest/",
            f"https://docs.{package_name}.org/",
            f"https://{package_name}.org/docs/",
            f"https://pypi.org/project/{package_name}/",
        ]

        # Return the first pattern for now (in a real implementation,
        # we might want to check which URLs are actually accessible)
        return common_patterns[0]

    async def test_package_documentation(self, package_name: str, doc_url: str) -> dict:
        """Test scraping documentation for a specific package."""
        logger.info(f"Testing documentation scraping for {package_name}: {doc_url}")

        # Choose backend based on site complexity
        if any(
            complex_site in doc_url
            for complex_site in ["fastapi", "pydantic", "scrapy"]
        ):
            from src.backends.crawl4ai_backend import Crawl4AIConfig

            backend = Crawl4AIBackend(config=Crawl4AIConfig())
            backend_name = "crawl4ai"
        else:
            from src.backends.http_backend import HTTPBackendConfig

            backend = HTTPBackend(config=HTTPBackendConfig())
            backend_name = "http"

        # Set up crawler with content processing
        content_processor = ContentProcessor()
        quality_checker = QualityChecker()

        crawler = DocumentationCrawler(
            backend=backend,
            content_processor=content_processor,
            quality_checker=quality_checker,
        )

        # Configure crawl target
        target = CrawlTarget(
            url=doc_url,
            depth=2,  # Reasonable depth for documentation
            max_pages=10,  # Limit pages for testing
            content_types=["text/html"],  # Specify content types
            exclude_patterns=[],  # Empty exclude patterns
            include_patterns=[],  # Empty include patterns
        )

        start_time = time.time()

        try:
            result = await crawler.crawl(
                target_url=target.url,
                depth=target.depth,
                max_pages=target.max_pages,
                follow_external=False,
            )

            duration = time.time() - start_time

            # Analyze results
            analysis = {
                "package": package_name,
                "url": doc_url,
                "backend": backend_name,
                "success": True,
                "duration": duration,
                "documents_found": len(result.documents),
                "successful_crawls": result.stats.successful_crawls,
                "failed_crawls": result.stats.failed_crawls,
                "total_requests": result.stats.total_requests,
                "success_rate": result.stats.successful_crawls
                / max(1, result.stats.total_requests),
                "pages_per_second": len(result.documents) / max(0.001, duration),
                "content_quality": {},
                "issues": len(result.issues) if hasattr(result, "issues") else 0,
                "sample_content": "",
            }

            # Analyze content quality
            if result.documents:
                total_content_length = sum(len(doc.content) for doc in result.documents)
                avg_content_length = total_content_length / len(result.documents)

                analysis["content_quality"] = {
                    "total_content_length": total_content_length,
                    "avg_content_length": avg_content_length,
                    "has_substantial_content": avg_content_length > 500,
                    "documents_with_content": sum(
                        1 for doc in result.documents if len(doc.content) > 100
                    ),
                }

                # Get sample content from first document
                if result.documents[0].content:
                    sample = result.documents[0].content[:500]
                    analysis["sample_content"] = sample

            logger.info(
                f"✅ {package_name}: {len(result.documents)} docs in {duration:.2f}s"
            )
            return analysis

        except Exception as e:
            duration = time.time() - start_time
            logger.error(f"❌ {package_name}: Failed - {e}")

            return {
                "package": package_name,
                "url": doc_url,
                "backend": backend_name,
                "success": False,
                "duration": duration,
                "error": str(e),
                "documents_found": 0,
                "successful_crawls": 0,
                "failed_crawls": 1,
                "success_rate": 0.0,
                "pages_per_second": 0.0,
            }

    async def run_dependency_tests(self) -> dict:
        """Run documentation scraping tests for all dependencies."""
        dependencies = self.extract_dependencies_from_discovery()

        if not dependencies:
            logger.error("No dependencies found to test")
            return self.results

        # Combine main and dev dependencies for testing
        all_packages = []
        for _group, packages in dependencies.items():
            all_packages.extend(packages)

        # Remove duplicates and filter out packages without clear doc URLs
        unique_packages = list(set(all_packages))

        # Filter to packages we have documentation URLs for
        testable_packages = [
            pkg
            for pkg in unique_packages
            if pkg in self.doc_url_patterns or not pkg.startswith("pytest-")
        ]

        logger.info(f"Testing documentation for {len(testable_packages)} packages")

        # Limit concurrent tests to avoid overwhelming sites
        semaphore = asyncio.Semaphore(self.config.get("max_concurrent", 3))

        async def test_with_semaphore(package_name: str) -> tuple[str, dict]:
            async with semaphore:
                doc_url = self.get_documentation_url(package_name)
                if not doc_url:
                    return package_name, {"error": "No documentation URL found"}

                result = await self.test_package_documentation(package_name, doc_url)
                return package_name, result

        # Run tests concurrently
        tasks = [
            test_with_semaphore(pkg) for pkg in testable_packages[:10]
        ]  # Limit to 10 for testing
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Test failed with exception: {result}")
                continue

            package_name, test_result = result
            self.results["crawl_results"][package_name] = test_result

        # Generate summary
        self.generate_summary()

        return self.results

    def generate_summary(self):
        """Generate summary statistics."""
        crawl_results = self.results["crawl_results"]

        if not crawl_results:
            self.results["summary"] = {"error": "No test results to summarize"}
            return

        successful_tests = [
            r for r in crawl_results.values() if r.get("success", False)
        ]
        failed_tests = [
            r for r in crawl_results.values() if not r.get("success", False)
        ]

        total_documents = sum(r.get("documents_found", 0) for r in successful_tests)
        total_duration = sum(r.get("duration", 0) for r in crawl_results.values())
        avg_success_rate = sum(
            r.get("success_rate", 0) for r in successful_tests
        ) / max(1, len(successful_tests))

        self.results["summary"] = {
            "total_packages_tested": len(crawl_results),
            "successful_tests": len(successful_tests),
            "failed_tests": len(failed_tests),
            "success_rate": len(successful_tests) / len(crawl_results),
            "total_documents_crawled": total_documents,
            "total_duration": total_duration,
            "avg_crawl_success_rate": avg_success_rate,
            "overall_pages_per_second": total_documents / max(0.001, total_duration),
        }

        self.results["end_time"] = datetime.now().isoformat()

    def save_results(self, output_file: str):
        """Save test results to file."""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(self.results, f, indent=2, default=str)

        logger.info(f"Results saved to {output_path}")

    def generate_html_report(self, html_file: str):
        """Generate HTML report of test results."""
        html_content = self._generate_html_content()

        html_path = Path(html_file)
        html_path.parent.mkdir(parents=True, exist_ok=True)

        with open(html_path, "w") as f:
            f.write(html_content)

        logger.info(f"HTML report saved to {html_path}")

    def _generate_html_content(self) -> str:
        """Generate HTML content for the report."""
        summary = self.results.get("summary", {})
        crawl_results = self.results.get("crawl_results", {})

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>lib2docScrape Dependency Documentation Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .summary {{ background: #f0f0f0; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .success {{ color: green; }}
        .failure {{ color: red; }}
        .warning {{ color: orange; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .content-sample {{ max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
    </style>
</head>
<body>
    <h1>lib2docScrape Dependency Documentation Test Report</h1>

    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Total Packages Tested:</strong> {summary.get("total_packages_tested", 0)}</p>
        <p><strong>Successful Tests:</strong> <span class="success">{summary.get("successful_tests", 0)}</span></p>
        <p><strong>Failed Tests:</strong> <span class="failure">{summary.get("failed_tests", 0)}</span></p>
        <p><strong>Success Rate:</strong> {summary.get("success_rate", 0):.1%}</p>
        <p><strong>Total Documents Crawled:</strong> {summary.get("total_documents_crawled", 0)}</p>
        <p><strong>Overall Performance:</strong> {summary.get("overall_pages_per_second", 0):.2f} pages/sec</p>
    </div>

    <h2>Detailed Results</h2>
    <table>
        <tr>
            <th>Package</th>
            <th>Status</th>
            <th>Backend</th>
            <th>Documents</th>
            <th>Duration (s)</th>
            <th>Success Rate</th>
            <th>Content Quality</th>
            <th>Sample Content</th>
        </tr>
"""

        for package, result in crawl_results.items():
            status_class = "success" if result.get("success") else "failure"
            status_text = "✅ Success" if result.get("success") else "❌ Failed"

            content_quality = result.get("content_quality", {})
            quality_text = (
                f"{content_quality.get('avg_content_length', 0):.0f} chars avg"
                if content_quality
                else "N/A"
            )

            sample_content = (
                result.get("sample_content", "")[:100] + "..."
                if result.get("sample_content")
                else ""
            )

            html += f"""
        <tr>
            <td><strong>{package}</strong></td>
            <td class="{status_class}">{status_text}</td>
            <td>{result.get("backend", "N/A")}</td>
            <td>{result.get("documents_found", 0)}</td>
            <td>{result.get("duration", 0):.2f}</td>
            <td>{result.get("success_rate", 0):.1%}</td>
            <td>{quality_text}</td>
            <td class="content-sample">{sample_content}</td>
        </tr>
"""

        html += (
            """
    </table>

    <h2>Test Configuration</h2>
    <pre>"""
            + json.dumps(self.results.get("config", {}), indent=2)
            + """</pre>

    <p><em>Generated on """
            + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            + """</em></p>
</body>
</html>"""
        )

        return html


async def main():
    """Main entry point for dependency documentation testing."""
    parser = argparse.ArgumentParser(
        description="Test lib2docScrape with project dependencies"
    )

    parser.add_argument(
        "--output", default="reports/dependency-docs.json", help="Output JSON file"
    )
    parser.add_argument(
        "--html-report",
        default="reports/dependency-report.html",
        help="HTML report file",
    )
    parser.add_argument(
        "--timeout", type=int, default=120, help="Test timeout in seconds"
    )
    parser.add_argument(
        "--max-concurrent", type=int, default=3, help="Max concurrent tests"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Build configuration
    config = {
        "timeout": args.timeout,
        "max_concurrent": args.max_concurrent,
        "verbose": args.verbose,
    }

    # Create tester and run tests
    tester = DependencyDocumentationTester(config)

    try:
        logger.info("Starting dependency documentation tests...")
        results = await tester.run_dependency_tests()

        # Save results
        tester.save_results(args.output)
        tester.generate_html_report(args.html_report)

        # Print summary
        summary = results.get("summary", {})
        print("\n" + "=" * 60)
        print("DEPENDENCY DOCUMENTATION TEST SUMMARY")
        print("=" * 60)
        print(f"Packages tested: {summary.get('total_packages_tested', 0)}")
        print(f"Successful: {summary.get('successful_tests', 0)}")
        print(f"Failed: {summary.get('failed_tests', 0)}")
        print(f"Success rate: {summary.get('success_rate', 0):.1%}")
        print(f"Documents crawled: {summary.get('total_documents_crawled', 0)}")
        print(
            f"Performance: {summary.get('overall_pages_per_second', 0):.2f} pages/sec"
        )
        print(f"Report: {args.html_report}")
        print("=" * 60)

        return 0 if summary.get("successful_tests", 0) > 0 else 1

    except Exception as e:
        logger.error(f"Dependency testing failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
