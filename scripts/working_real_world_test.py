#!/usr/bin/env python3
"""
Working Real-World Test for lib2docScrape

Now that we understand the system, let's run a proper real-world test
using our discovered dependencies with all backends.
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


class WorkingRealWorldTest:
    """Working real-world test with proper configuration."""

    def __init__(self):
        self.test_results = {
            "start_time": datetime.now().isoformat(),
            "backend_tests": {},
            "dependency_tests": {},
            "storage_analysis": {},
            "performance_metrics": {},
            "lessons_learned": [],
        }

        # Test dependencies from our discovery
        self.test_dependencies = {
            "requests": "https://requests.readthedocs.io/en/latest/",
            "beautifulsoup4": "https://www.crummy.com/software/BeautifulSoup/bs4/doc/",
            "pytest": "https://docs.pytest.org/en/stable/",
        }

    async def test_backend_with_dependency(
        self,
        backend_name: str,
        backend_class,
        config_class,
        package_name: str,
        url: str,
    ):
        """Test a specific backend with a dependency's documentation."""
        logger.info(f"🧪 Testing {backend_name} with {package_name}")

        test_result = {
            "backend": backend_name,
            "package": package_name,
            "url": url,
            "success": False,
            "metrics": {},
            "content_info": {},
            "storage_info": {},
        }

        try:
            # Initialize backend with proper config
            config = config_class() if config_class else None
            if config:
                backend = backend_class(config=config)
            else:
                backend = backend_class()

            # Create DocumentationCrawler
            from src.crawler import DocumentationCrawler

            crawler = DocumentationCrawler(backend=backend)

            # Perform crawl with individual parameters (not CrawlTarget object)
            start_time = time.time()
            result = await crawler.crawl(
                target_url=url,
                depth=1,
                follow_external=False,
                content_types=["text/html"],
                exclude_patterns=[],
                required_patterns=[],
                max_pages=3,
                allowed_paths=[],
                excluded_paths=[],
            )
            duration = time.time() - start_time

            # Analyze results
            total_requests = result.stats.successful_crawls + result.stats.failed_crawls
            test_result["metrics"] = {
                "duration": duration,
                "documents_found": len(result.documents),
                "successful_crawls": result.stats.successful_crawls,
                "failed_crawls": result.stats.failed_crawls,
                "pages_crawled": result.stats.pages_crawled,
                "total_requests": total_requests,
                "success_rate": result.stats.successful_crawls / max(1, total_requests),
            }

            # Analyze content
            if result.documents:
                first_doc = result.documents[0]
                content = first_doc.get("content", "")
                test_result["content_info"] = {
                    "first_doc_title": first_doc.get("title", "No title"),
                    "content_length": len(str(content)),
                    "has_substantial_content": len(str(content)) > 500,
                    "sample_content": str(content)[:200] + "..."
                    if len(str(content)) > 200
                    else str(content),
                }

                test_result["success"] = True
                logger.info(
                    f"✅ {backend_name} + {package_name}: {len(result.documents)} docs in {duration:.2f}s"
                )
            else:
                logger.warning(
                    f"⚠️  {backend_name} + {package_name}: No documents found"
                )

            # Check for output files
            archive_files = (
                list(Path("archive").glob("*.json")) if Path("archive").exists() else []
            )
            test_result["storage_info"] = {
                "archive_files_count": len(archive_files),
                "latest_archive_file": str(
                    max(archive_files, key=lambda f: f.stat().st_mtime)
                )
                if archive_files
                else None,
            }

            await backend.close()

        except Exception as e:
            test_result["error"] = str(e)
            logger.error(f"❌ {backend_name} + {package_name}: {e}")

        return test_result

    async def test_all_backends(self):
        """Test all available backends with our dependencies."""
        logger.info("🚀 Testing all backends with real dependencies...")

        # Backend configurations
        backends_to_test = [
            (
                "HTTPBackend",
                "src.backends.http_backend",
                "HTTPBackend",
                "HTTPBackendConfig",
            ),
            (
                "Crawl4AIBackend",
                "src.backends.crawl4ai",
                "Crawl4AIBackend",
                "Crawl4AIConfig",
            ),
            ("FileBackend", "src.backends.file_backend", "FileBackend", None),
        ]

        for backend_name, module_path, class_name, config_name in backends_to_test:
            logger.info(f"\n--- Testing {backend_name} ---")

            try:
                # Import backend and config
                module = __import__(module_path, fromlist=[class_name])
                backend_class = getattr(module, class_name)
                config_class = getattr(module, config_name) if config_name else None

                # Test with one dependency
                package_name = "requests"
                url = self.test_dependencies[package_name]

                test_result = await self.test_backend_with_dependency(
                    backend_name, backend_class, config_class, package_name, url
                )

                self.test_results["backend_tests"][backend_name] = test_result

                # Brief pause between backend tests
                await asyncio.sleep(2)

            except Exception as e:
                logger.error(f"❌ Failed to test {backend_name}: {e}")
                self.test_results["backend_tests"][backend_name] = {
                    "error": str(e),
                    "success": False,
                }

    async def analyze_storage_output(self):
        """Analyze what content has been stored."""
        logger.info("🔍 Analyzing stored content...")

        storage_analysis = {
            "archive_directory": {},
            "docs_directory": {},
            "recent_outputs": [],
            "content_samples": [],
        }

        # Analyze archive directory
        if Path("archive").exists():
            archive_files = list(Path("archive").glob("*.json"))
            storage_analysis["archive_directory"] = {
                "total_files": len(archive_files),
                "total_size_mb": sum(f.stat().st_size for f in archive_files)
                / 1024
                / 1024,
                "oldest_file": str(min(archive_files, key=lambda f: f.stat().st_mtime))
                if archive_files
                else None,
                "newest_file": str(max(archive_files, key=lambda f: f.stat().st_mtime))
                if archive_files
                else None,
            }

            # Sample recent files
            recent_files = sorted(
                archive_files, key=lambda f: f.stat().st_mtime, reverse=True
            )[:3]
            for file_path in recent_files:
                try:
                    with open(file_path) as f:
                        data = json.load(f)

                    storage_analysis["recent_outputs"].append(
                        {
                            "file": str(file_path),
                            "size_kb": file_path.stat().st_size / 1024,
                            "documents_count": len(data.get("documents", [])),
                            "target_url": data.get("target", {}).get("url", "Unknown"),
                            "stats": data.get("stats", {}),
                        }
                    )
                except Exception as e:
                    logger.warning(f"Could not read {file_path}: {e}")

        # Analyze docs directory
        if Path("docs").exists():
            docs_files = list(Path("docs").glob("*"))
            storage_analysis["docs_directory"] = {
                "total_files": len(docs_files),
                "file_types": list({f.suffix for f in docs_files if f.is_file()}),
            }

        self.test_results["storage_analysis"] = storage_analysis
        return storage_analysis

    async def run_comprehensive_test(self):
        """Run comprehensive real-world test."""
        logger.info("🎯 Starting comprehensive real-world test...")

        # Test all backends
        await self.test_all_backends()

        # Analyze storage
        await self.analyze_storage_output()

        # Generate performance summary
        self.generate_performance_summary()

        return self.test_results

    def generate_performance_summary(self):
        """Generate performance summary from test results."""
        backend_tests = self.test_results["backend_tests"]

        performance_metrics = {
            "successful_backends": 0,
            "total_documents_crawled": 0,
            "average_crawl_time": 0,
            "best_performing_backend": None,
            "backend_comparison": {},
        }

        successful_tests = []

        for backend_name, test_result in backend_tests.items():
            if test_result.get("success"):
                performance_metrics["successful_backends"] += 1
                metrics = test_result.get("metrics", {})

                successful_tests.append(
                    {
                        "backend": backend_name,
                        "duration": metrics.get("duration", 0),
                        "documents": metrics.get("documents_found", 0),
                        "success_rate": metrics.get("success_rate", 0),
                    }
                )

                performance_metrics["total_documents_crawled"] += metrics.get(
                    "documents_found", 0
                )

                performance_metrics["backend_comparison"][backend_name] = {
                    "documents": metrics.get("documents_found", 0),
                    "duration": metrics.get("duration", 0),
                    "pages_per_second": metrics.get("documents_found", 0)
                    / max(0.001, metrics.get("duration", 0.001)),
                }

        if successful_tests:
            performance_metrics["average_crawl_time"] = sum(
                t["duration"] for t in successful_tests
            ) / len(successful_tests)

            # Find best performing backend (by pages per second)
            best_backend = max(
                successful_tests,
                key=lambda x: x["documents"] / max(0.001, x["duration"]),
            )
            performance_metrics["best_performing_backend"] = best_backend["backend"]

        self.test_results["performance_metrics"] = performance_metrics

    def save_results(self, filename: str = "reports/working_real_world_test.json"):
        """Save test results."""
        self.test_results["end_time"] = datetime.now().isoformat()

        output_path = Path(filename)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(self.test_results, f, indent=2, default=str)

        logger.info(f"📄 Results saved to {output_path}")
        return output_path


async def main():
    """Main function for working real-world test."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.info("=" * 60)
    logger.info("🎯 WORKING REAL-WORLD TEST")
    logger.info("=" * 60)
    logger.info("Testing lib2docScrape with discovered dependencies")
    logger.info("Using all available backends with proper configuration")
    logger.info("=" * 60)

    try:
        tester = WorkingRealWorldTest()
        results = await tester.run_comprehensive_test()

        # Save results
        report_path = tester.save_results()

        # Print summary
        print("\n" + "=" * 60)
        print("🎯 REAL-WORLD TEST RESULTS")
        print("=" * 60)

        # Backend results
        backend_tests = results["backend_tests"]
        successful_backends = sum(
            1 for test in backend_tests.values() if test.get("success")
        )
        print(f"📦 Backends tested: {len(backend_tests)}")
        print(f"✅ Successful: {successful_backends}")
        print(f"❌ Failed: {len(backend_tests) - successful_backends}")

        for backend_name, test_result in backend_tests.items():
            if test_result.get("success"):
                metrics = test_result.get("metrics", {})
                docs = metrics.get("documents_found", 0)
                duration = metrics.get("duration", 0)
                print(f"  ✅ {backend_name}: {docs} docs in {duration:.2f}s")
            else:
                print(f"  ❌ {backend_name}: Failed")

        # Storage results
        storage = results.get("storage_analysis", {})
        archive_info = storage.get("archive_directory", {})
        if archive_info:
            print("\n💾 Storage Analysis:")
            print(f"  Archive files: {archive_info.get('total_files', 0)}")
            print(f"  Total size: {archive_info.get('total_size_mb', 0):.1f} MB")

        # Performance summary
        performance = results.get("performance_metrics", {})
        if performance:
            print("\n🚀 Performance Summary:")
            print(
                f"  Total documents crawled: {performance.get('total_documents_crawled', 0)}"
            )
            print(
                f"  Average crawl time: {performance.get('average_crawl_time', 0):.2f}s"
            )
            if performance.get("best_performing_backend"):
                print(f"  Best backend: {performance['best_performing_backend']}")

        print(f"\n📄 Full report: {report_path}")
        print("=" * 60)

        return 0 if successful_backends > 0 else 1

    except Exception as e:
        logger.error(f"💥 Real-world test failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
