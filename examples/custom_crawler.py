#!/usr/bin/env python3
"""
Example script demonstrating how to use the documentation crawler programmatically
with custom configurations and handlers.
"""

import asyncio
import logging
from typing import Dict, List

from pydantic import BaseModel

from src.backends.crawl4ai import Crawl4AIBackend, Crawl4AIConfig
from src.backends.selector import BackendCriteria, BackendSelector
from src.crawler import CrawlerConfig, CrawlTarget, DocumentationCrawler
from src.organizers.doc_organizer import DocumentOrganizer, OrganizationConfig
from src.processors.content_processor import ContentProcessor, ProcessedContent
from src.processors.quality_checker import QualityChecker, QualityConfig
from src.utils.helpers import Timer, setup_logging


class CustomDocumentHandler:
    """Example custom handler for processed documents."""
    
    def __init__(self, output_dir: str = "output"):
        self.output_dir = output_dir
        self.processed_docs: List[Dict] = []

    async def handle_document(self, content: ProcessedContent) -> None:
        """
        Handle a processed document.
        
        Args:
            content: Processed document content
        """
        # Example: Store document metadata
        doc_info = {
            "url": content.url,
            "title": content.title,
            "metadata": content.metadata,
            "assets": content.assets
        }
        self.processed_docs.append(doc_info)
        
        # Log processing
        logging.info(f"Processed document: {content.title} ({content.url})")

    def get_statistics(self) -> Dict:
        """
        Get processing statistics.
        
        Returns:
            Dictionary of statistics
        """
        return {
            "total_documents": len(self.processed_docs),
            "unique_urls": len(set(doc["url"] for doc in self.processed_docs)),
            "total_assets": sum(
                len(doc["assets"].get("images", [])) +
                len(doc["assets"].get("scripts", [])) +
                len(doc["assets"].get("stylesheets", []))
                for doc in self.processed_docs
            )
        }


class CustomQualityHandler:
    """Example custom handler for quality issues."""
    
    def __init__(self):
        self.issues_by_severity: Dict[str, List[Dict]] = {
            "error": [],
            "warning": [],
            "info": []
        }

    async def handle_issue(self, doc_url: str, issue: Dict) -> None:
        """
        Handle a quality issue.
        
        Args:
            doc_url: URL of the document with the issue
            issue: Quality issue details
        """
        issue_info = {
            "url": doc_url,
            "message": issue["message"],
            "location": issue.get("location"),
            "context": issue.get("context")
        }
        self.issues_by_severity[issue["severity"]].append(issue_info)
        
        # Log severe issues
        if issue["severity"] == "error":
            logging.error(f"Quality issue in {doc_url}: {issue['message']}")

    def get_summary(self) -> Dict:
        """
        Get issue summary.
        
        Returns:
            Dictionary summarizing quality issues
        """
        return {
            severity: len(issues)
            for severity, issues in self.issues_by_severity.items()
        }


async def main():
    """Example usage of the documentation crawler."""
    # Setup logging
    setup_logging(level="INFO")
    
    # Initialize custom handlers
    doc_handler = CustomDocumentHandler()
    quality_handler = CustomQualityHandler()
    
    # Configure crawler components
    crawler_config = CrawlerConfig(
        concurrent_requests=3,
        requests_per_second=1.0,
        max_retries=2,
        request_timeout=20.0
    )
    
    # Configure backend
    backend_selector = BackendSelector()
    crawl4ai_backend = Crawl4AIBackend(
        config=Crawl4AIConfig(
            max_retries=2,
            timeout=20.0
        )
    )
    
    # Register backend with criteria
    backend_selector.register_backend(
        crawl4ai_backend,
        BackendCriteria(
            priority=100,
            content_types=["text/html"],
            url_patterns=["*"],
            max_load=0.8,
            min_success_rate=0.7
        )
    )
    
    # Initialize crawler with components
    crawler = DocumentationCrawler(
        config=crawler_config,
        backend_selector=backend_selector,
        content_processor=ContentProcessor(),
        quality_checker=QualityChecker(
            config=QualityConfig(
                min_content_length=50,
                max_broken_links_ratio=0.2
            )
        ),
        document_organizer=DocumentOrganizer(
            config=OrganizationConfig(
                min_similarity_score=0.3,
                max_versions_to_keep=5
            )
        )
    )
    
    # Define crawl targets
    targets = [
        CrawlTarget(
            url="https://docs.python.org/3/library/asyncio.html",
            depth=1,
            follow_external=False,
            content_types=["text/html"],
            exclude_patterns=["/download/", "/bugs/"],
            required_patterns=["/library/"],
            max_pages=10
        ),
        CrawlTarget(
            url="https://docs.aiohttp.org/en/stable/client.html",
            depth=1,
            follow_external=False,
            content_types=["text/html"],
            exclude_patterns=["/contributing/"],
            required_patterns=["/client/"],
            max_pages=5
        )
    ]
    
    try:
        # Process each target
        for target in targets:
            logging.info(f"Starting crawl for {target.url}")
            
            with Timer(f"Crawling {target.url}") as timer:
                result = await crawler.crawl(target)
            
            logging.info(
                f"Completed crawl of {target.url}:"
                f" {result.stats.pages_crawled} pages,"
                f" {result.stats.successful_crawls} successful,"
                f" {result.stats.failed_crawls} failed"
            )
            
            # Process documents and quality issues
            for doc_id in result.documents:
                # Example: Get document from organizer and process it
                doc = crawler.document_organizer.documents.get(doc_id)
                if doc:
                    # Handle document content
                    content = ProcessedContent(
                        url=doc.url,
                        title=doc.title,
                        content={},  # Would contain actual content
                        metadata=doc.versions[-1].changes,
                        assets={}
                    )
                    await doc_handler.handle_document(content)
            
            # Handle quality issues
            for issue in result.issues:
                await quality_handler.handle_issue(target.url, issue.dict())
        
        # Output results
        logging.info("\nProcessing Statistics:")
        logging.info(f"Documents: {doc_handler.get_statistics()}")
        logging.info(f"Quality Issues: {quality_handler.get_summary()}")
        
    finally:
        # Cleanup
        await crawler.close()


if __name__ == "__main__":
    asyncio.run(main())