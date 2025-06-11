#!/usr/bin/env python3
"""
Comprehensive Diagnostic Test for lib2docScrape Real-World Testing

This script provides detailed diagnostics to understand:
1. What backends are available and being used
2. Where scraped content is being saved
3. What's happening during the crawling process
4. Performance and storage metrics
"""

import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

logger = logging.getLogger(__name__)


class ComprehensiveDiagnostic:
    """Comprehensive diagnostic for real-world testing."""

    def __init__(self):
        self.diagnostic_results = {
            "timestamp": datetime.now().isoformat(),
            "system_info": {},
            "backend_analysis": {},
            "storage_analysis": {},
            "crawl_test_results": {},
            "file_system_analysis": {},
            "recommendations": [],
        }

    async def analyze_available_backends(self):
        """Analyze what backends are available and functional."""
        logger.info("🔍 Analyzing available backends...")

        backend_analysis = {
            "available_backends": [],
            "backend_configs": {},
            "backend_instances": {},
            "import_status": {},
        }

        # Test backend imports
        backends_to_test = [
            ("HTTPBackend", "src.backends.http_backend", "HTTPBackend"),
            ("Crawl4AIBackend", "src.backends.crawl4ai", "Crawl4AIBackend"),
            (
                "PlaywrightBackend",
                "src.backends.playwright_backend",
                "PlaywrightBackend",
            ),
            ("ScrapyBackend", "src.backends.scrapy_backend", "ScrapyBackend"),
            ("FileBackend", "src.backends.file_backend", "FileBackend"),
            (
                "LightpandaBackend",
                "src.backends.lightpanda_backend",
                "LightpandaBackend",
            ),
        ]

        for backend_name, module_path, class_name in backends_to_test:
            try:
                module = __import__(module_path, fromlist=[class_name])
                getattr(module, class_name)
                backend_analysis["import_status"][backend_name] = "✅ Available"
                backend_analysis["available_backends"].append(backend_name)

                # Try to get config class if it exists
                config_class_name = f"{class_name}Config"
                if hasattr(module, config_class_name):
                    getattr(module, config_class_name)
                    backend_analysis["backend_configs"][
                        backend_name
                    ] = config_class_name

                logger.info(f"✅ {backend_name}: Available")

            except ImportError as e:
                backend_analysis["import_status"][
                    backend_name
                ] = f"❌ Import Error: {e}"
                logger.warning(f"❌ {backend_name}: Import failed - {e}")
            except Exception as e:
                backend_analysis["import_status"][backend_name] = f"❌ Error: {e}"
                logger.error(f"❌ {backend_name}: Error - {e}")

        self.diagnostic_results["backend_analysis"] = backend_analysis
        return backend_analysis

    async def analyze_storage_mechanisms(self):
        """Analyze where and how content is stored."""
        logger.info("🔍 Analyzing storage mechanisms...")

        storage_analysis = {
            "output_directories": {},
            "storage_classes": {},
            "config_storage_settings": {},
        }

        # Check common output directories
        output_dirs_to_check = [
            "docs",
            "output",
            "crawl_results",
            "documentation",
            "scraped_content",
            "data",
            "results",
        ]

        for dir_name in output_dirs_to_check:
            dir_path = Path(dir_name)
            storage_analysis["output_directories"][dir_name] = {
                "exists": dir_path.exists(),
                "is_dir": dir_path.is_dir() if dir_path.exists() else False,
                "file_count": len(list(dir_path.glob("*")))
                if dir_path.exists() and dir_path.is_dir()
                else 0,
            }

        # Check storage classes
        storage_classes_to_test = [
            ("CompressedStorage", "src.storage.compressed.storage"),
            ("DocumentOrganizer", "src.organizers.doc_organizer"),
        ]

        for class_name, module_path in storage_classes_to_test:
            try:
                module = __import__(module_path, fromlist=[class_name])
                getattr(module, class_name)
                storage_analysis["storage_classes"][class_name] = "✅ Available"
                logger.info(f"✅ Storage class {class_name}: Available")
            except Exception as e:
                storage_analysis["storage_classes"][class_name] = f"❌ Error: {e}"
                logger.warning(f"❌ Storage class {class_name}: Error - {e}")

        # Check config files for storage settings
        config_files = [
            "src/config/presets/default.yaml",
            "src/config/presets/minimal.yaml",
        ]
        for config_file in config_files:
            if Path(config_file).exists():
                storage_analysis["config_storage_settings"][config_file] = "Found"
            else:
                storage_analysis["config_storage_settings"][config_file] = "Not found"

        self.diagnostic_results["storage_analysis"] = storage_analysis
        return storage_analysis

    async def test_single_backend_crawl(
        self, backend_name: str, test_url: str = "https://httpbin.org/html"
    ):
        """Test a single backend with detailed logging."""
        logger.info(f"🧪 Testing {backend_name} backend...")

        test_result = {
            "backend": backend_name,
            "test_url": test_url,
            "success": False,
            "error": None,
            "metrics": {},
            "content_info": {},
            "storage_info": {},
        }

        try:
            # Import and initialize backend
            if backend_name == "HTTPBackend":
                from src.backends.http_backend import HTTPBackend, HTTPBackendConfig

                config = HTTPBackendConfig()
                backend = HTTPBackend(config=config)
            else:
                test_result["error"] = f"Backend {backend_name} not implemented in test"
                return test_result

            # Create URL info
            from src.utils.url import create_url_info

            url_info = create_url_info(test_url)

            # Test direct backend crawl
            start_time = time.time()
            crawl_result = await backend.crawl(url_info, config=None)
            crawl_duration = time.time() - start_time

            # Analyze results
            test_result["metrics"] = {
                "crawl_duration": crawl_duration,
                "status_code": crawl_result.status,
                "has_content": bool(crawl_result.content),
                "content_keys": list(crawl_result.content.keys())
                if crawl_result.content
                else [],
                "metadata_keys": list(crawl_result.metadata.keys())
                if crawl_result.metadata
                else [],
            }

            if crawl_result.content and "html" in crawl_result.content:
                html_content = crawl_result.content["html"]
                test_result["content_info"] = {
                    "html_length": len(html_content),
                    "has_title": "<title>" in html_content.lower(),
                    "has_body": "<body>" in html_content.lower(),
                    "sample_content": html_content[:200] + "..."
                    if len(html_content) > 200
                    else html_content,
                }

            test_result["success"] = crawl_result.status == 200

            # Test with DocumentationCrawler
            from src.crawler import CrawlTarget, DocumentationCrawler

            crawler = DocumentationCrawler(backend=backend)

            target = CrawlTarget(url=test_url, depth=1, max_pages=1)

            start_time = time.time()
            crawler_result = await crawler.crawl(
                target_url=target.url,
                depth=target.depth,
                max_pages=target.max_pages,
                follow_external=False,
            )
            crawler_duration = time.time() - start_time

            test_result["crawler_metrics"] = {
                "crawler_duration": crawler_duration,
                "documents_found": len(crawler_result.documents),
                "successful_crawls": crawler_result.stats.successful_crawls,
                "failed_crawls": crawler_result.stats.failed_crawls,
                "total_requests": crawler_result.stats.total_requests,
            }

            # Check if any files were created
            current_files = list(Path(".").glob("*"))
            test_result["storage_info"]["files_in_current_dir"] = len(current_files)

            # Check for output files
            output_patterns = ["*.json", "crawl_result_*.json", "docs/*", "output/*"]
            found_files = []
            for pattern in output_patterns:
                found_files.extend(list(Path(".").glob(pattern)))

            test_result["storage_info"]["output_files_found"] = [
                str(f) for f in found_files
            ]

            await backend.close()

        except Exception as e:
            test_result["error"] = str(e)
            logger.error(f"❌ {backend_name} test failed: {e}")

        return test_result

    async def analyze_file_system_changes(self):
        """Analyze what files are created during testing."""
        logger.info("🔍 Analyzing file system for scraped content...")

        file_analysis = {
            "current_directory_files": [],
            "potential_output_directories": {},
            "recent_files": [],
            "json_files": [],
            "log_files": [],
        }

        # List current directory files
        current_files = list(Path(".").glob("*"))
        file_analysis["current_directory_files"] = [
            str(f) for f in current_files if f.is_file()
        ]

        # Check for potential output directories
        for item in current_files:
            if item.is_dir():
                file_count = len(list(item.glob("*")))
                file_analysis["potential_output_directories"][str(item)] = file_count

        # Find JSON files (likely crawl results)
        json_files = list(Path(".").rglob("*.json"))
        file_analysis["json_files"] = [str(f) for f in json_files]

        # Find log files
        log_files = list(Path(".").rglob("*.log"))
        file_analysis["log_files"] = [str(f) for f in log_files]

        # Find recently modified files (last 10 minutes)
        import time

        current_time = time.time()
        recent_threshold = current_time - 600  # 10 minutes

        for file_path in Path(".").rglob("*"):
            if file_path.is_file():
                try:
                    if file_path.stat().st_mtime > recent_threshold:
                        file_analysis["recent_files"].append(
                            {
                                "path": str(file_path),
                                "size": file_path.stat().st_size,
                                "modified": datetime.fromtimestamp(
                                    file_path.stat().st_mtime
                                ).isoformat(),
                            }
                        )
                except OSError:
                    pass  # Skip files we can't access

        self.diagnostic_results["file_system_analysis"] = file_analysis
        return file_analysis

    async def run_comprehensive_diagnostic(self):
        """Run complete diagnostic analysis."""
        logger.info("🚀 Starting comprehensive diagnostic...")

        # System info
        self.diagnostic_results["system_info"] = {
            "python_version": sys.version,
            "current_directory": str(Path.cwd()),
            "environment_variables": {
                "PYTHONPATH": os.environ.get("PYTHONPATH", "Not set"),
                "PATH": os.environ.get("PATH", "Not set")[:200] + "..."
                if len(os.environ.get("PATH", "")) > 200
                else os.environ.get("PATH", "Not set"),
            },
        }

        # Run all analyses
        await self.analyze_available_backends()
        await self.analyze_storage_mechanisms()
        await self.analyze_file_system_changes()

        # Test a backend
        backend_analysis = self.diagnostic_results["backend_analysis"]
        if "HTTPBackend" in backend_analysis["available_backends"]:
            test_result = await self.test_single_backend_crawl("HTTPBackend")
            self.diagnostic_results["crawl_test_results"]["HTTPBackend"] = test_result

        # Generate recommendations
        self.generate_recommendations()

        return self.diagnostic_results

    def generate_recommendations(self):
        """Generate recommendations based on diagnostic results."""
        recommendations = []

        backend_analysis = self.diagnostic_results["backend_analysis"]
        storage_analysis = self.diagnostic_results["storage_analysis"]

        # Backend recommendations
        available_count = len(backend_analysis["available_backends"])
        if available_count == 0:
            recommendations.append(
                "❌ CRITICAL: No backends are available. Check import paths and dependencies."
            )
        elif available_count == 1:
            recommendations.append(
                "⚠️  WARNING: Only one backend available. Consider installing additional backends for redundancy."
            )
        else:
            recommendations.append(
                f"✅ GOOD: {available_count} backends available for testing."
            )

        # Storage recommendations
        storage_classes = storage_analysis["storage_classes"]
        available_storage = sum(
            1 for status in storage_classes.values() if "Available" in status
        )
        if available_storage == 0:
            recommendations.append(
                "❌ CRITICAL: No storage classes available. Content may not be saved."
            )
        else:
            recommendations.append(
                f"✅ GOOD: {available_storage} storage mechanisms available."
            )

        # File system recommendations
        file_analysis = self.diagnostic_results.get("file_system_analysis", {})
        if file_analysis.get("json_files"):
            recommendations.append(
                f"✅ GOOD: Found {len(file_analysis['json_files'])} JSON files - content is being saved."
            )
        else:
            recommendations.append(
                "⚠️  WARNING: No JSON output files found. Check if content is being saved."
            )

        self.diagnostic_results["recommendations"] = recommendations

    def save_diagnostic_report(self, filename: str = "reports/diagnostic_report.json"):
        """Save comprehensive diagnostic report."""
        output_path = Path(filename)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(self.diagnostic_results, f, indent=2, default=str)

        logger.info(f"📄 Diagnostic report saved to {output_path}")
        return output_path


async def main():
    """Main diagnostic function."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.info("=" * 60)
    logger.info("🔍 COMPREHENSIVE DIAGNOSTIC TEST")
    logger.info("=" * 60)

    try:
        diagnostic = ComprehensiveDiagnostic()
        results = await diagnostic.run_comprehensive_diagnostic()

        # Save report
        report_path = diagnostic.save_diagnostic_report()

        # Print summary
        print("\n" + "=" * 60)
        print("🔍 DIAGNOSTIC SUMMARY")
        print("=" * 60)

        # Backend summary
        backend_analysis = results["backend_analysis"]
        print(f"📦 Available Backends: {len(backend_analysis['available_backends'])}")
        for backend in backend_analysis["available_backends"]:
            print(f"  ✅ {backend}")

        # Storage summary
        storage_analysis = results["storage_analysis"]
        available_storage = sum(
            1
            for status in storage_analysis["storage_classes"].values()
            if "Available" in status
        )
        print(f"💾 Storage Mechanisms: {available_storage}")

        # File system summary
        file_analysis = results.get("file_system_analysis", {})
        print(f"📁 JSON Files Found: {len(file_analysis.get('json_files', []))}")
        print(f"📁 Recent Files: {len(file_analysis.get('recent_files', []))}")

        # Test results
        if "crawl_test_results" in results:
            for backend, test_result in results["crawl_test_results"].items():
                status = "✅ SUCCESS" if test_result["success"] else "❌ FAILED"
                print(f"🧪 {backend} Test: {status}")
                if test_result.get("metrics"):
                    duration = test_result["metrics"].get("crawl_duration", 0)
                    print(f"   Duration: {duration:.2f}s")

        # Recommendations
        print("\n💡 RECOMMENDATIONS:")
        for rec in results["recommendations"]:
            print(f"  {rec}")

        print(f"\n📄 Full report: {report_path}")
        print("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"💥 Diagnostic failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
