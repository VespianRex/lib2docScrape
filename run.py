#!/usr/bin/env python3
"""Main entry point for the lib2docscrape application."""

import asyncio
import logging
from pathlib import Path

import yaml

from src.backends.crawl4ai_backend import Crawl4AIBackend, Crawl4AIConfig
from src.backends.selector import BackendSelector
from src.utils.helpers import normalize_url

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler("crawler.log"), logging.StreamHandler()],
)

logger = logging.getLogger(__name__)


async def main():
    """Main function to run the crawler."""
    # Load configuration
    config_path = Path("config.yaml")
    if not config_path.exists():
        raise FileNotFoundError("config.yaml not found")

    with open(config_path) as f:
        config = yaml.safe_load(f)

    # Initialize backend selector
    selector = BackendSelector()

    # Configure and initialize Crawl4AI backend
    crawl4ai_config = Crawl4AIConfig(
        max_retries=config.get("max_retries", 3),
        timeout=config.get("timeout", 30.0),
        headers=config.get(
            "headers", {"User-Agent": "Crawl4AI/1.0 Documentation Crawler"}
        ),
        follow_redirects=config.get("follow_redirects", True),
        verify_ssl=config.get("verify_ssl", True),
        max_depth=config.get("max_depth", 5),
    )

    Crawl4AIBackend(config=crawl4ai_config)

    # Start crawling from target URLs
    targets = config.get("targets", [])
    for target in targets:
        try:
            url_info = normalize_url(target)
            if not url_info.is_valid:
                logger.warning(f"Invalid URL: {target}")
                continue

            backend = await selector.select_backend(target)
            if not backend:
                logger.warning(f"No suitable backend found for: {target}")
                continue

            result = await backend.crawl(url_info)
            logger.info(f"Successfully crawled: {target}")
            logger.debug(f"Crawl result: {result}")
        except Exception as e:
            logger.error(f"Error crawling {target}: {str(e)}")


if __name__ == "__main__":
    asyncio.run(main())
