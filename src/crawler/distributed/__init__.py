"""
Distributed crawling capabilities for lib2docScrape.
"""

from .manager import DistributedCrawlManager
from .models import DistributedConfig, TaskResult, WorkerStatus, WorkerTask
from .worker import CrawlWorker

__all__ = [
    "CrawlWorker",
    "DistributedCrawlManager",
    "WorkerTask",
    "TaskResult",
    "WorkerStatus",
    "DistributedConfig",
]
