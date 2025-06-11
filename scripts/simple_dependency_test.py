#!/usr/bin/env python3
"""
Simple test of lib2docScrape using project dependencies.

This script tests our system by scraping a few key library documentation sites.
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


async def test_simple_docs():
    """Test scraping some simple documentation sites."""

    # Test sites - start with simple ones
    test_sites = {
        "requests": "https://requests.readthedocs.io/en/latest/",
        "beautifulsoup4": "https://www.crummy.com/software/BeautifulSoup/bs4/doc/",
        "pytest": "https://docs.pytest.org/en/stable/",
    }

    results = {}

    for package, url in test_sites.items():
        logger.info(f"Testing {package}: {url}")

        try:
            # Create simple backend (no config needed for basic HTTP)
            backend = HTTPBackend()
            crawler = DocumentationCrawler(backend=backend)

            # Simple crawl target
            target = CrawlTarget(url=url, depth=1, max_pages=3)

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
            results[package] = {
                "success": True,
                "url": url,
                "duration": duration,
                "documents": len(result.documents),
                "successful_crawls": result.stats.successful_crawls,
                "failed_crawls": result.stats.failed_crawls,
                "sample_content": result.documents[0].content[:200]
                if result.documents
                else "",
            }

            logger.info(
                f"✅ {package}: {len(result.documents)} docs in {duration:.2f}s"
            )

        except Exception as e:
            logger.error(f"❌ {package}: Failed - {e}")
            results[package] = {
                "success": False,
                "url": url,
                "error": str(e),
                "duration": time.time() - start_time if "start_time" in locals() else 0,
            }

    return results


async def main():
    """Main function."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.info("Starting simple dependency documentation test...")

    try:
        results = await test_simple_docs()

        # Print summary
        successful = sum(1 for r in results.values() if r.get("success", False))
        total = len(results)

        print("\n" + "=" * 50)
        print("SIMPLE DEPENDENCY TEST RESULTS")
        print("=" * 50)
        print(f"Total tests: {total}")
        print(f"Successful: {successful}")
        print(f"Failed: {total - successful}")
        print(f"Success rate: {successful / total:.1%}")

        for package, result in results.items():
            status = "✅" if result.get("success") else "❌"
            duration = result.get("duration", 0)
            docs = result.get("documents", 0)
            print(f"{status} {package}: {docs} docs in {duration:.2f}s")

        print("=" * 50)

        # Save results
        output_file = "reports/simple-dependency-test.json"
        Path(output_file).parent.mkdir(parents=True, exist_ok=True)

        with open(output_file, "w") as f:
            json.dump(
                {
                    "timestamp": datetime.now().isoformat(),
                    "results": results,
                    "summary": {
                        "total": total,
                        "successful": successful,
                        "success_rate": successful / total,
                    },
                },
                f,
                indent=2,
            )

        print(f"Results saved to: {output_file}")

        return 0 if successful > 0 else 1

    except Exception as e:
        logger.error(f"Test failed: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
