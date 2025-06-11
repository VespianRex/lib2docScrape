#!/usr/bin/env python3
"""Debug script to test DuckDuckGo initialization."""

from unittest.mock import patch

from src.crawler import CrawlerConfig, DocumentationCrawler

print("Creating config with use_duckduckgo=True...")
config = CrawlerConfig(max_depth=2, max_pages=10, use_duckduckgo=True)
print(f"Config use_duckduckgo: {config.use_duckduckgo}")
print(f"Config duckduckgo_max_results: {config.duckduckgo_max_results}")

print("\nPatching DuckDuckGoSearch...")
with patch("src.utils.search.DuckDuckGoSearch") as mock_ddg_class:
    print("Creating DocumentationCrawler...")
    crawler = DocumentationCrawler(config=config)

    print(f"DuckDuckGoSearch call count: {mock_ddg_class.call_count}")
    print(f"DuckDuckGoSearch called: {mock_ddg_class.called}")
    print(f"Crawler duckduckgo attribute: {crawler.duckduckgo}")

    if mock_ddg_class.called:
        print("SUCCESS: DuckDuckGoSearch was called!")
    else:
        print("FAILURE: DuckDuckGoSearch was NOT called!")
