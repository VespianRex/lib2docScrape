#!/usr/bin/env python3
"""
First Real-World Test Run for lib2docScrape

This script performs our first careful real-world test using discovered dependencies.
We'll be extra careful and learn as much as possible from this initial run.
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

logger = logging.getLogger(__name__)


class FirstRealWorldTest:
    """Manages our first careful real-world test run."""

    def __init__(self):
        self.test_results = {
            "start_time": datetime.now().isoformat(),
            "test_phase": "initialization",
            "discoveries": [],
            "issues_found": [],
            "successes": [],
            "lessons_learned": [],
            "next_steps": [],
        }

        # Start with a small, safe set of dependencies for first run
        self.safe_test_dependencies = {
            "requests": {
                "url": "https://requests.readthedocs.io/en/latest/",
                "reason": "Well-established, stable documentation site",
                "expected_complexity": "low",
            },
            "beautifulsoup4": {
                "url": "https://www.crummy.com/software/BeautifulSoup/bs4/doc/",
                "reason": "Simple static documentation",
                "expected_complexity": "low",
            },
        }

    def log_discovery(self, message: str, details: dict = None):
        """Log a discovery from our testing."""
        discovery = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "details": details or {},
        }
        self.test_results["discoveries"].append(discovery)
        logger.info(f"🔍 DISCOVERY: {message}")
        if details:
            logger.info(f"   Details: {details}")

    def log_issue(self, message: str, error: str = None, suggestion: str = None):
        """Log an issue found during testing."""
        issue = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "error": error,
            "suggestion": suggestion,
        }
        self.test_results["issues_found"].append(issue)
        logger.error(f"❌ ISSUE: {message}")
        if error:
            logger.error(f"   Error: {error}")
        if suggestion:
            logger.info(f"   💡 Suggestion: {suggestion}")

    def log_success(self, message: str, metrics: dict = None):
        """Log a success from our testing."""
        success = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "metrics": metrics or {},
        }
        self.test_results["successes"].append(success)
        logger.info(f"✅ SUCCESS: {message}")
        if metrics:
            logger.info(f"   Metrics: {metrics}")

    def log_lesson(self, lesson: str, impact: str = None):
        """Log a lesson learned."""
        lesson_entry = {
            "timestamp": datetime.now().isoformat(),
            "lesson": lesson,
            "impact": impact,
        }
        self.test_results["lessons_learned"].append(lesson_entry)
        logger.info(f"📚 LESSON: {lesson}")
        if impact:
            logger.info(f"   Impact: {impact}")

    async def test_basic_imports(self):
        """Test that we can import our core modules."""
        self.test_results["test_phase"] = "basic_imports"
        logger.info("🧪 Testing basic imports...")

        try:
            from src.backends.http_backend import HTTPBackendConfig

            self.log_success("HTTPBackend imports working")

            self.log_success("Crawler imports working")

            # Test basic config creation
            config = HTTPBackendConfig()
            self.log_success(
                "HTTPBackendConfig creation working",
                {
                    "timeout": config.timeout,
                    "verify_ssl": config.verify_ssl,
                    "follow_redirects": config.follow_redirects,
                },
            )

            return True

        except Exception as e:
            self.log_issue(
                "Basic imports failed",
                str(e),
                "Check import paths and module structure",
            )
            return False

    async def test_backend_initialization(self):
        """Test backend initialization with proper configuration."""
        self.test_results["test_phase"] = "backend_initialization"
        logger.info("🧪 Testing backend initialization...")

        try:
            from src.backends.http_backend import HTTPBackend, HTTPBackendConfig

            # Test with default config
            config = HTTPBackendConfig()
            backend = HTTPBackend(config=config)

            self.log_success(
                "HTTPBackend initialization successful",
                {"backend_name": backend.name, "config_timeout": config.timeout},
            )

            # Test crawler initialization
            from src.crawler import DocumentationCrawler

            crawler = DocumentationCrawler(backend=backend)

            self.log_success("DocumentationCrawler initialization successful")

            return backend, crawler

        except Exception as e:
            self.log_issue(
                "Backend initialization failed",
                str(e),
                "Check backend configuration requirements",
            )
            return None, None

    async def test_crawl_target_creation(self):
        """Test CrawlTarget creation with proper parameters."""
        self.test_results["test_phase"] = "crawl_target_creation"
        logger.info("🧪 Testing CrawlTarget creation...")

        try:
            from src.crawler import CrawlTarget

            # Test with minimal required parameters
            target = CrawlTarget(url="https://example.com", depth=1, max_pages=1)

            self.log_success(
                "Basic CrawlTarget creation successful",
                {
                    "url": target.url,
                    "depth": target.depth,
                    "max_pages": target.max_pages,
                },
            )

            # Test with full parameters
            CrawlTarget(
                url="https://example.com",
                depth=1,
                max_pages=1,
                content_types=["text/html"],
                exclude_patterns=[],
                include_patterns=[],
            )

            self.log_success("Full CrawlTarget creation successful")

            return True

        except Exception as e:
            self.log_issue(
                "CrawlTarget creation failed",
                str(e),
                "Check CrawlTarget parameter requirements",
            )
            return False

    async def test_single_dependency(
        self, package_name: str, package_info: dict, backend, crawler
    ):
        """Test scraping a single dependency's documentation."""
        logger.info(f"🧪 Testing {package_name} documentation...")

        try:
            from src.crawler import CrawlTarget

            # Create crawl target
            target = CrawlTarget(
                url=package_info["url"],
                depth=1,
                max_pages=2,  # Keep it small for first test
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
            metrics = {
                "duration": duration,
                "documents_found": len(result.documents),
                "successful_crawls": result.stats.successful_crawls,
                "failed_crawls": result.stats.failed_crawls,
                "total_requests": result.stats.total_requests,
            }

            if result.documents:
                first_doc = result.documents[0]
                metrics.update(
                    {
                        "first_doc_length": len(first_doc.content),
                        "first_doc_url": first_doc.url,
                        "sample_content": first_doc.content[:200] + "..."
                        if first_doc.content
                        else "",
                    }
                )

                self.log_success(
                    f"{package_name} documentation scraped successfully", metrics
                )

                # Analyze content quality
                if len(first_doc.content) > 100:
                    self.log_discovery(
                        f"{package_name} has substantial content",
                        {
                            "content_length": len(first_doc.content),
                            "has_html_tags": "<html>" in first_doc.content.lower(),
                        },
                    )
                else:
                    self.log_issue(
                        f"{package_name} content seems minimal",
                        f"Only {len(first_doc.content)} characters",
                        "Check if content extraction is working properly",
                    )
            else:
                self.log_issue(
                    f"{package_name} returned no documents",
                    f"Stats: {metrics}",
                    "Check URL accessibility and crawl parameters",
                )

            return True, metrics

        except Exception as e:
            self.log_issue(
                f"{package_name} test failed",
                str(e),
                "Check network connectivity and site accessibility",
            )
            return False, {}

    async def run_first_test(self):
        """Run our first careful real-world test."""
        logger.info("🚀 Starting first real-world test run...")

        # Phase 1: Basic functionality tests
        if not await self.test_basic_imports():
            return False

        backend, crawler = await self.test_backend_initialization()
        if not backend or not crawler:
            return False

        if not await self.test_crawl_target_creation():
            return False

        # Phase 2: Real-world dependency testing
        self.test_results["test_phase"] = "dependency_testing"

        for package_name, package_info in self.safe_test_dependencies.items():
            logger.info(f"\n--- Testing {package_name} ---")
            success, metrics = await test_single_dependency(
                package_name, package_info, backend, crawler
            )

            if success:
                self.log_lesson(
                    f"{package_name} test revealed system capabilities",
                    f"Successfully processed {metrics.get('documents_found', 0)} documents",
                )

            # Brief pause between tests to be respectful
            await asyncio.sleep(2)

        # Phase 3: Cleanup and analysis
        try:
            await backend.close()
            self.log_success("Backend cleanup completed")
        except Exception as e:
            self.log_issue("Backend cleanup failed", str(e))

        return True

    def generate_report(self):
        """Generate comprehensive test report."""
        self.test_results["end_time"] = datetime.now().isoformat()
        self.test_results["test_phase"] = "completed"

        # Add summary
        self.test_results["summary"] = {
            "total_discoveries": len(self.test_results["discoveries"]),
            "total_issues": len(self.test_results["issues_found"]),
            "total_successes": len(self.test_results["successes"]),
            "total_lessons": len(self.test_results["lessons_learned"]),
        }

        return self.test_results

    def save_report(self, filename: str):
        """Save detailed test report."""
        report = self.generate_report()

        output_path = Path(filename)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2)

        logger.info(f"📄 Detailed report saved to {output_path}")


async def test_single_dependency(
    package_name: str, package_info: dict, backend, crawler
):
    """Helper function for testing single dependency."""
    try:
        from src.crawler import CrawlTarget

        target = CrawlTarget(url=package_info["url"], depth=1, max_pages=2)

        start_time = time.time()

        result = await crawler.crawl(
            target_url=target.url,
            depth=target.depth,
            max_pages=target.max_pages,
            follow_external=False,
        )

        duration = time.time() - start_time

        metrics = {
            "duration": duration,
            "documents_found": len(result.documents),
            "successful_crawls": result.stats.successful_crawls,
            "failed_crawls": result.stats.failed_crawls,
            "total_requests": result.stats.total_requests,
        }

        return True, metrics

    except Exception as e:
        logger.error(f"Error testing {package_name}: {e}")
        return False, {}


async def main():
    """Main function for first real-world test."""
    # Configure detailed logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("reports/first_real_test.log"),
        ],
    )

    logger.info("=" * 60)
    logger.info("🎯 FIRST REAL-WORLD TEST RUN")
    logger.info("=" * 60)
    logger.info("This is our first careful test using discovered dependencies.")
    logger.info("We'll be extra careful and learn from every step.")
    logger.info("=" * 60)

    try:
        tester = FirstRealWorldTest()
        success = await tester.run_first_test()

        # Generate and save report
        tester.save_report("reports/first_real_world_test.json")

        # Print summary
        report = tester.generate_report()
        summary = report["summary"]

        print("\n" + "=" * 60)
        print("🎯 FIRST REAL-WORLD TEST SUMMARY")
        print("=" * 60)
        print(f"✅ Successes: {summary['total_successes']}")
        print(f"❌ Issues Found: {summary['total_issues']}")
        print(f"🔍 Discoveries: {summary['total_discoveries']}")
        print(f"📚 Lessons Learned: {summary['total_lessons']}")

        if report["successes"]:
            print("\n🎉 Key Successes:")
            for success in report["successes"][-3:]:  # Show last 3
                print(f"  • {success['message']}")

        if report["issues_found"]:
            print("\n⚠️  Issues to Address:")
            for issue in report["issues_found"][-3:]:  # Show last 3
                print(f"  • {issue['message']}")
                if issue.get("suggestion"):
                    print(f"    💡 {issue['suggestion']}")

        if report["lessons_learned"]:
            print("\n📚 Key Lessons:")
            for lesson in report["lessons_learned"][-3:]:  # Show last 3
                print(f"  • {lesson['lesson']}")

        print("\n📄 Detailed report: reports/first_real_world_test.json")
        print("📄 Log file: reports/first_real_test.log")
        print("=" * 60)

        return 0 if success else 1

    except Exception as e:
        logger.error(f"💥 First real-world test failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
