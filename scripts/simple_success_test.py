#!/usr/bin/env python3
"""
Simple Success Test for lib2docScrape

This script performs a simple test to verify the system is working
and can successfully scrape documentation.
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


async def simple_test():
    """Run a simple test to verify the system works."""
    logger.info("🧪 Starting simple success test...")

    try:
        # Import required modules
        from src.backends.http_backend import HTTPBackend, HTTPBackendConfig
        from src.crawler import DocumentationCrawler

        # Create backend with config
        config = HTTPBackendConfig()
        backend = HTTPBackend(config=config)

        # Create crawler
        crawler = DocumentationCrawler(backend=backend)

        # Test with a simple, reliable site
        test_url = "https://httpbin.org/html"

        logger.info(f"🎯 Testing with: {test_url}")

        start_time = time.time()

        # Perform crawl
        result = await crawler.crawl(
            target_url=test_url,
            depth=1,
            follow_external=False,
            content_types=["text/html"],
            exclude_patterns=[],
            required_patterns=[],
            max_pages=1,
            allowed_paths=[],
            excluded_paths=[],
        )

        duration = time.time() - start_time

        # Analyze results
        logger.info(f"⏱️  Crawl completed in {duration:.2f} seconds")
        logger.info(f"📄 Documents found: {len(result.documents)}")
        logger.info(f"✅ Successful crawls: {result.stats.successful_crawls}")
        logger.info(f"❌ Failed crawls: {result.stats.failed_crawls}")
        logger.info(f"📊 Pages crawled: {result.stats.pages_crawled}")

        # Check if we got content
        if result.documents:
            first_doc = result.documents[0]
            content = first_doc.get("content", "")
            content_length = len(str(content))

            logger.info("📝 First document:")
            logger.info(f"   Title: {first_doc.get('title', 'No title')}")
            logger.info(f"   Content length: {content_length} characters")
            logger.info(f"   URL: {first_doc.get('url', 'No URL')}")

            if content_length > 100:
                logger.info("✅ SUCCESS: Got substantial content!")

                # Save a sample result
                sample_result = {
                    "timestamp": datetime.now().isoformat(),
                    "test_url": test_url,
                    "duration": duration,
                    "documents_count": len(result.documents),
                    "successful_crawls": result.stats.successful_crawls,
                    "failed_crawls": result.stats.failed_crawls,
                    "pages_crawled": result.stats.pages_crawled,
                    "content_sample": str(content)[:500] + "..."
                    if content_length > 500
                    else str(content),
                    "success": True,
                }

                # Save to reports
                Path("reports").mkdir(exist_ok=True)
                with open("reports/simple_success_test.json", "w") as f:
                    json.dump(sample_result, f, indent=2)

                logger.info(
                    "📄 Sample result saved to reports/simple_success_test.json"
                )

                return True
            else:
                logger.warning("⚠️  Got content but it's very short")
                return False
        else:
            logger.error("❌ No documents found")
            return False

    except Exception as e:
        logger.error(f"💥 Test failed: {e}")
        return False

    finally:
        try:
            await backend.close()
            logger.info("🔧 Backend closed")
        except Exception:
            pass


async def main():
    """Main function."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    logger.info("=" * 50)
    logger.info("🎯 SIMPLE SUCCESS TEST")
    logger.info("=" * 50)
    logger.info("Testing if lib2docScrape can successfully scrape content")
    logger.info("=" * 50)

    success = await simple_test()

    if success:
        print("\n" + "=" * 50)
        print("🎉 SUCCESS! lib2docScrape is working!")
        print("✅ The system can successfully:")
        print("   • Initialize backends")
        print("   • Create crawlers")
        print("   • Scrape web content")
        print("   • Process and extract content")
        print("   • Return structured results")
        print("=" * 50)
        return 0
    else:
        print("\n" + "=" * 50)
        print("❌ FAILED! Something is not working correctly")
        print("Check the logs above for details")
        print("=" * 50)
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
