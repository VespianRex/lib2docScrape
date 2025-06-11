#!/usr/bin/env python3
import asyncio
from unittest.mock import AsyncMock

from src.backends.base import CrawlResult
from src.crawler.crawler import DocumentationCrawler
from src.crawler.models import CrawlTarget


async def test_debug():
    processor = AsyncMock()
    processor.process = AsyncMock(side_effect=ValueError("Invalid content"))

    mock_quality_checker = AsyncMock()
    mock_doc_organizer = AsyncMock()

    crawler = DocumentationCrawler(
        quality_checker=mock_quality_checker,
        document_organizer=mock_doc_organizer,
        content_processor=processor,
    )

    target = CrawlTarget(url="https://test.com")
    mock_backend = AsyncMock()
    mock_backend.crawl = AsyncMock(
        return_value=CrawlResult(
            url="https://test.com",
            content={"html": "Invalid content"},
            metadata={},
            status=200,
        )
    )

    try:
        result = await crawler.crawl(target, backend=mock_backend)
        print(f"result.errors: {result.errors}")
        print(f"result.stats.failed_crawls: {result.stats.failed_crawls}")
        print(f"result.crawled_urls: {result.crawled_urls}")
        print(f"result.failed_urls: {result.failed_urls}")
    except Exception as e:
        print(f"Exception during crawl: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_debug())
