#!/usr/bin/env python3
import argparse
import asyncio
import json
import logging
import os
from typing import Any, Dict, Optional

import yaml
from pydantic import BaseModel

from .backends.crawl4ai import Crawl4AIBackend, Crawl4AIConfig
from .backends.selector import BackendCriteria, BackendSelector
from .crawler import CrawlerConfig, CrawlTarget, DocumentationCrawler
from .organizers.doc_organizer import DocumentOrganizer, OrganizationConfig
from .processors.content_processor import ContentProcessor, ProcessingConfig
from .processors.quality_checker import QualityChecker, QualityConfig
from .utils.helpers import setup_logging


class AppConfig(BaseModel):
    """Application configuration model."""
    crawler: CrawlerConfig
    processing: ProcessingConfig
    quality: QualityConfig
    organization: OrganizationConfig
    crawl4ai: Crawl4AIConfig
    logging: Dict[str, Any]


def load_config(config_path: str) -> AppConfig:
    """
    Load configuration from file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Loaded configuration
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r') as f:
        if config_path.endswith('.json'):
            config_data = json.load(f)
        elif config_path.endswith('.yaml') or config_path.endswith('.yml'):
            config_data = yaml.safe_load(f)
        else:
            raise ValueError("Configuration file must be JSON or YAML")
    
    return AppConfig(**config_data)


def setup_crawler(config: AppConfig) -> DocumentationCrawler:
    """
    Setup crawler with configuration.
    
    Args:
        config: Application configuration
        
    Returns:
        Configured DocumentationCrawler instance
    """
    # Initialize components
    backend_selector = BackendSelector()
    content_processor = ContentProcessor(config=config.processing)
    quality_checker = QualityChecker(config=config.quality)
    document_organizer = DocumentOrganizer(config=config.organization)
    
    # Setup Crawl4AI backend
    crawl4ai_backend = Crawl4AIBackend(config=config.crawl4ai)
    backend_selector.register_backend(
        crawl4ai_backend,
        BackendCriteria(
            priority=100,
            content_types=["text/html", "text/plain"],
            url_patterns=["*"],
            max_load=0.8,
            min_success_rate=0.7
        )
    )
    
    # Create and return crawler
    return DocumentationCrawler(
        config=config.crawler,
        backend_selector=backend_selector,
        content_processor=content_processor,
        quality_checker=quality_checker,
        document_organizer=document_organizer
    )


async def run_crawler(
    crawler: DocumentationCrawler,
    targets: list[CrawlTarget]
) -> None:
    """
    Run crawler for specified targets.
    
    Args:
        crawler: Configured crawler instance
        targets: List of crawl targets
    """
    try:
        for target in targets:
            logging.info(f"Starting crawl for target: {target.url}")
            result = await crawler.crawl(target)
            
            logging.info(f"Crawl completed for {target.url}")
            logging.info(f"Pages crawled: {result.stats.pages_crawled}")
            logging.info(f"Successful crawls: {result.stats.successful_crawls}")
            logging.info(f"Failed crawls: {result.stats.failed_crawls}")
            logging.info(f"Quality issues: {result.stats.quality_issues}")
            logging.info(
                f"Average time per page: {result.stats.average_time_per_page:.2f}s"
            )
            
            # Output results
            output_file = f"crawl_result_{result.stats.start_time:%Y%m%d_%H%M%S}.json"
            with open(output_file, 'w') as f:
                json.dump(
                    {
                        "target": target.dict(),
                        "stats": result.stats.dict(),
                        "documents": result.documents,
                        "issues": [issue.dict() for issue in result.issues],
                        "metrics": {
                            k: v.dict() for k, v in result.metrics.items()
                        }
                    },
                    f,
                    indent=2,
                    default=str
                )
            logging.info(f"Results saved to {output_file}")
    
    finally:
        await crawler.close()


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments.
    
    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Documentation Crawler CLI"
    )
    
    parser.add_argument(
        '-c', '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file (JSON or YAML)'
    )
    
    parser.add_argument(
        '-t', '--targets',
        type=str,
        required=True,
        help='Path to targets file (JSON or YAML)'
    )
    
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    return parser.parse_args()


def load_targets(targets_path: str) -> list[CrawlTarget]:
    """
    Load crawl targets from file.
    
    Args:
        targets_path: Path to targets file
        
    Returns:
        List of crawl targets
    """
    if not os.path.exists(targets_path):
        raise FileNotFoundError(f"Targets file not found: {targets_path}")
    
    with open(targets_path, 'r') as f:
        if targets_path.endswith('.json'):
            targets_data = json.load(f)
        elif targets_path.endswith('.yaml') or targets_path.endswith('.yml'):
            targets_data = yaml.safe_load(f)
        else:
            raise ValueError("Targets file must be JSON or YAML")
    
    return [CrawlTarget(**target) for target in targets_data]


def main() -> None:
    """Main entry point."""
    # Parse arguments
    args = parse_args()
    
    try:
        # Load configuration
        config = load_config(args.config)
        
        # Setup logging
        log_level = "DEBUG" if args.verbose else config.logging.get("level", "INFO")
        setup_logging(
            level=log_level,
            log_file=config.logging.get("file"),
            format_string=config.logging.get("format")
        )
        
        # Load targets
        targets = load_targets(args.targets)
        
        # Setup and run crawler
        crawler = setup_crawler(config)
        asyncio.run(run_crawler(crawler, targets))
        
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        raise


if __name__ == "__main__":
    main()