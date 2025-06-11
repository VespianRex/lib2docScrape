#!/usr/bin/env python3
"""
Test lib2docScrape using discovered project dependencies.

This script uses the dependency discovery tool to find all project dependencies
and then tests our scraping system against their documentation sites.
"""

import asyncio
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.backends.http_backend import HTTPBackend  # noqa: E402
from src.crawler import CrawlTarget, DocumentationCrawler  # noqa: E402

logger = logging.getLogger(__name__)


class DiscoveredDependencyTester:
    """Tests lib2docScrape using discovered dependencies."""

    def __init__(self):
        self.doc_url_patterns = {
            "requests": "https://requests.readthedocs.io/en/latest/",
            "aiohttp": "https://docs.aiohttp.org/en/stable/",
            "beautifulsoup4": "https://www.crummy.com/software/BeautifulSoup/bs4/doc/",
            "pytest": "https://docs.pytest.org/en/stable/",
            "fastapi": "https://fastapi.tiangolo.com/",
            "pydantic": "https://docs.pydantic.dev/latest/",
            "scrapy": "https://docs.scrapy.org/en/latest/",
            "markdownify": "https://pypi.org/project/markdownify/",
            "bleach": "https://bleach.readthedocs.io/en/latest/",
            "tldextract": "https://github.com/john-kurkowski/tldextract",
            "psutil": "https://psutil.readthedocs.io/en/latest/",
            "httpx": "https://www.python-httpx.org/",
            "ruff": "https://docs.astral.sh/ruff/",
            "coverage": "https://coverage.readthedocs.io/en/latest/",
            "jinja2": "https://jinja.palletsprojects.com/",
            "uvloop": "https://github.com/MagicStack/uvloop",
        }

    def load_discovered_dependencies(
        self, discovery_file: str = "reports/discovered-deps.json"
    ) -> list:
        """Load dependencies from discovery report."""
        try:
            with open(discovery_file) as f:
                data = json.load(f)

            # Get main dependencies from config files
            config_deps = (
                data.get("dependencies", {})
                .get("by_source", {})
                .get("config_files", {})
            )
            main_deps = config_deps.get("main", [])

            # Filter to packages we have documentation URLs for
            testable_deps = [dep for dep in main_deps if dep in self.doc_url_patterns]

            logger.info(
                f"Found {len(testable_deps)} testable dependencies from {len(main_deps)} main dependencies"
            )
            return testable_deps

        except Exception as e:
            logger.error(f"Failed to load discovered dependencies: {e}")
            # Fallback to a few key packages
            return ["requests", "beautifulsoup4", "pytest"]

    async def test_dependency_docs(self, package: str, url: str) -> dict:
        """Test scraping documentation for a specific dependency."""
        logger.info(f"Testing {package}: {url}")

        try:
            # Create simple backend with default config
            from src.backends.http_backend import HTTPBackendConfig

            backend = HTTPBackend(config=HTTPBackendConfig())
            crawler = DocumentationCrawler(backend=backend)

            # Simple crawl target
            target = CrawlTarget(
                url=url,
                depth=1,
                max_pages=3,
                content_types=["text/html"],
                exclude_patterns=[],
                include_patterns=[],
            )

            start_time = time.time()

            # Perform crawl
            result = await crawler.crawl(
                target_url=target.url,
                depth=target.depth,
                max_pages=target.max_pages,
                follow_external=False,
            )

            duration = time.time() - start_time

            # Analyze results
            return {
                "package": package,
                "url": url,
                "success": True,
                "duration": duration,
                "documents": len(result.documents),
                "successful_crawls": result.stats.successful_crawls,
                "failed_crawls": result.stats.failed_crawls,
                "success_rate": result.stats.successful_crawls
                / max(1, result.stats.total_requests),
                "sample_content": result.documents[0].content[:200]
                if result.documents
                else "",
                "content_length": sum(len(doc.content) for doc in result.documents),
            }

        except Exception as e:
            logger.error(f"❌ {package}: Failed - {e}")
            return {
                "package": package,
                "url": url,
                "success": False,
                "error": str(e),
                "duration": time.time() - start_time if "start_time" in locals() else 0,
            }

    async def run_tests(self) -> dict:
        """Run tests for all discovered dependencies."""
        # Load discovered dependencies
        dependencies = self.load_discovered_dependencies()

        if not dependencies:
            logger.error("No testable dependencies found")
            return {"error": "No dependencies to test"}

        logger.info(f"Testing {len(dependencies)} dependencies")

        results = {}

        # Test each dependency sequentially to be respectful to servers
        for package in dependencies:
            url = self.doc_url_patterns[package]
            result = await self.test_dependency_docs(package, url)
            results[package] = result

            # Brief pause between requests
            await asyncio.sleep(1)

        return results

    def generate_report(self, results: dict) -> dict:
        """Generate test report."""
        if "error" in results:
            return {"error": results["error"]}

        successful = [r for r in results.values() if r.get("success", False)]
        failed = [r for r in results.values() if not r.get("success", False)]

        total_docs = sum(r.get("documents", 0) for r in successful)
        total_content = sum(r.get("content_length", 0) for r in successful)
        total_duration = sum(r.get("duration", 0) for r in results.values())

        return {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_tested": len(results),
                "successful": len(successful),
                "failed": len(failed),
                "success_rate": len(successful) / len(results),
                "total_documents": total_docs,
                "total_content_length": total_content,
                "total_duration": total_duration,
                "avg_docs_per_package": total_docs / max(1, len(successful)),
                "pages_per_second": total_docs / max(0.001, total_duration),
            },
            "results": results,
        }

    def save_report(self, report: dict, output_file: str):
        """Save test report."""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"Report saved to {output_path}")

    def generate_html_report(self, report: dict, html_file: str):
        """Generate HTML report."""
        if "error" in report:
            html_content = (
                f"<html><body><h1>Error</h1><p>{report['error']}</p></body></html>"
            )
        else:
            summary = report["summary"]
            results = report["results"]

            html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Discovered Dependencies Test Report</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .summary {{ background: #f0f0f0; padding: 15px; border-radius: 5px; margin-bottom: 20px; }}
        .success {{ color: green; }}
        .failure {{ color: red; }}
        table {{ border-collapse: collapse; width: 100%; }}
        th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
        th {{ background-color: #f2f2f2; }}
        .sample {{ max-width: 300px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }}
    </style>
</head>
<body>
    <h1>Discovered Dependencies Test Report</h1>

    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Total Tested:</strong> {summary["total_tested"]}</p>
        <p><strong>Successful:</strong> <span class="success">{summary["successful"]}</span></p>
        <p><strong>Failed:</strong> <span class="failure">{summary["failed"]}</span></p>
        <p><strong>Success Rate:</strong> {summary["success_rate"]:.1%}</p>
        <p><strong>Total Documents:</strong> {summary["total_documents"]}</p>
        <p><strong>Performance:</strong> {summary["pages_per_second"]:.2f} pages/sec</p>
    </div>

    <h2>Test Results</h2>
    <table>
        <tr>
            <th>Package</th>
            <th>Status</th>
            <th>Documents</th>
            <th>Duration (s)</th>
            <th>Success Rate</th>
            <th>Content Length</th>
            <th>Sample Content</th>
        </tr>
"""

            for package, result in results.items():
                status_class = "success" if result.get("success") else "failure"
                status_text = "✅ Success" if result.get("success") else "❌ Failed"
                sample = (
                    result.get("sample_content", "")[:100] + "..."
                    if result.get("sample_content")
                    else ""
                )

                html_content += f"""
        <tr>
            <td><strong>{package}</strong></td>
            <td class="{status_class}">{status_text}</td>
            <td>{result.get("documents", 0)}</td>
            <td>{result.get("duration", 0):.2f}</td>
            <td>{result.get("success_rate", 0):.1%}</td>
            <td>{result.get("content_length", 0):,}</td>
            <td class="sample">{sample}</td>
        </tr>
"""

            html_content += (
                """
    </table>

    <p><em>Generated on """
                + datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                + """</em></p>
</body>
</html>"""
            )

        html_path = Path(html_file)
        html_path.parent.mkdir(parents=True, exist_ok=True)

        with open(html_path, "w") as f:
            f.write(html_content)

        logger.info(f"HTML report saved to {html_path}")


async def main():
    """Main function."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.info("Starting discovered dependencies test...")

    try:
        tester = DiscoveredDependencyTester()

        # Run tests
        results = await tester.run_tests()

        # Generate report
        report = tester.generate_report(results)

        # Save reports
        tester.save_report(report, "reports/discovered-deps-test.json")
        tester.generate_html_report(report, "reports/discovered-deps-test.html")

        # Print summary
        if "error" not in report:
            summary = report["summary"]

            print("\n" + "=" * 60)
            print("DISCOVERED DEPENDENCIES TEST RESULTS")
            print("=" * 60)
            print(f"Total tested: {summary['total_tested']}")
            print(f"Successful: {summary['successful']}")
            print(f"Failed: {summary['failed']}")
            print(f"Success rate: {summary['success_rate']:.1%}")
            print(f"Total documents: {summary['total_documents']}")
            print(f"Performance: {summary['pages_per_second']:.2f} pages/sec")

            print("\nDetailed results:")
            for package, result in report["results"].items():
                status = "✅" if result.get("success") else "❌"
                docs = result.get("documents", 0)
                duration = result.get("duration", 0)
                print(f"{status} {package}: {docs} docs in {duration:.2f}s")

            print("\nReports saved:")
            print("  JSON: reports/discovered-deps-test.json")
            print("  HTML: reports/discovered-deps-test.html")
            print("=" * 60)

            return 0 if summary["successful"] > 0 else 1
        else:
            print(f"Error: {report['error']}")
            return 1

    except Exception as e:
        logger.error(f"Test failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
