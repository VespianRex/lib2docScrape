"""
Distributed crawling capabilities for lib2docScrape.
"""
from .worker import CrawlWorker
from .manager import DistributedCrawlManager
from .models import WorkerTask, TaskResult, WorkerStatus, DistributedConfig

__all__ = [
    'CrawlWorker',
    'DistributedCrawlManager',
    'WorkerTask',
    'TaskResult',
    'WorkerStatus',
    'DistributedConfig'
]
