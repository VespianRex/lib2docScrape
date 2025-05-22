"""
Crawler module for lib2docScrape.
"""
from .models import CrawlTarget, CrawlConfig, CrawlResult, CrawlStats, QualityIssue
from .crawler import Crawler

# Define aliases for backward compatibility
DocumentationCrawler = Crawler
CrawlerConfig = CrawlConfig

__all__ = [
    'CrawlTarget',
    'CrawlConfig',
    'Crawler',
    'DocumentationCrawler',
    'CrawlerConfig',
    'CrawlResult',
    'CrawlStats',
    'QualityIssue'
]
