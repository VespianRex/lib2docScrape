"""
Runner for distributed crawling.
"""
import asyncio
import logging
import os
import signal
import sys
import time
from typing import Dict, List, Optional, Any, Set, Tuple

from .manager import DistributedCrawlManager
from .worker import CrawlWorker
from .models import WorkerTask, TaskResult, WorkerStatus, DistributedConfig
from ...backends.selector import BackendSelector
from ...crawler import CrawlTarget

logger = logging.getLogger(__name__)

class DistributedCrawlRunner:
    """
    Runner for distributed crawling.
    Coordinates the manager and workers for distributed crawling.
    """
    
    def __init__(self, config: Optional[DistributedConfig] = None):
        """
        Initialize the runner.
        
        Args:
            config: Optional configuration
        """
        self.config = config or DistributedConfig()
        self.manager = DistributedCrawlManager(config=self.config)
        self.workers: Dict[str, CrawlWorker] = {}
        self.backend_selector = BackendSelector()
        self.running = False
        self.tasks: List[asyncio.Task] = []
        
        logger.info(f"Distributed crawl runner initialized with max_workers={self.config.max_workers}")
        
    async def start_manager(self) -> None:
        """Start the manager."""
        logger.info("Starting manager")
        self.manager_task = asyncio.create_task(self.manager.run())
        self.tasks.append(self.manager_task)
        
    async def start_worker(self, worker_id: Optional[str] = None) -> CrawlWorker:
        """
        Start a worker.
        
        Args:
            worker_id: Optional worker ID
            
        Returns:
            Worker instance
        """
        # Create worker
        worker = CrawlWorker(
            worker_id=worker_id,
            backend_selector=self.backend_selector,
            task_callback=self.manager.complete_task,
            heartbeat_callback=self.manager.update_worker_heartbeat
        )
        
        # Register worker with manager
        await self.manager.register_worker(worker.get_info())
        
        # Start heartbeat loop
        heartbeat_task = asyncio.create_task(
            worker.run_heartbeat_loop(interval=self.config.heartbeat_interval)
        )
        self.tasks.append(heartbeat_task)
        
        # Store worker
        self.workers[worker.worker_id] = worker
        
        logger.info(f"Started worker {worker.worker_id}")
        
        return worker
        
    async def start_workers(self, num_workers: int) -> None:
        """
        Start multiple workers.
        
        Args:
            num_workers: Number of workers to start
        """
        logger.info(f"Starting {num_workers} workers")
        
        for i in range(num_workers):
            worker_id = f"worker_{i+1}"
            await self.start_worker(worker_id)
            
    async def add_crawl_targets(self, targets: List[CrawlTarget]) -> None:
        """
        Add crawl targets to the manager.
        
        Args:
            targets: List of crawl targets
        """
        logger.info(f"Adding {len(targets)} crawl targets")
        
        for target in targets:
            # Create task
            task = WorkerTask(
                url=target.url,
                max_depth=target.depth,
                priority=10,
                metadata={
                    "follow_external": target.follow_external,
                    "content_types": target.content_types,
                    "exclude_patterns": target.exclude_patterns
                }
            )
            
            # Add task to manager
            self.manager.add_task(task)
            
    async def run(self, targets: List[CrawlTarget], num_workers: int) -> None:
        """
        Run distributed crawling.
        
        Args:
            targets: List of crawl targets
            num_workers: Number of workers to start
        """
        self.running = True
        
        # Set up signal handlers
        self._setup_signal_handlers()
        
        try:
            # Start manager
            await self.start_manager()
            
            # Start workers
            await self.start_workers(num_workers)
            
            # Add crawl targets
            await self.add_crawl_targets(targets)
            
            # Wait for completion
            while self.running:
                # Check if all tasks are complete
                if (len(self.manager.task_queue) == 0 and 
                    len(self.manager.running_tasks) == 0):
                    logger.info("All tasks completed")
                    break
                    
                # Wait a bit
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            logger.info("Distributed crawling cancelled")
        except Exception as e:
            logger.error(f"Error in distributed crawling: {e}")
        finally:
            # Shutdown
            await self.shutdown()
            
    async def shutdown(self) -> None:
        """Shutdown the runner."""
        logger.info("Shutting down distributed crawl runner")
        
        # Shutdown workers
        for worker_id, worker in self.workers.items():
            try:
                await worker.shutdown()
            except Exception as e:
                logger.error(f"Error shutting down worker {worker_id}: {e}")
                
        # Cancel tasks
        for task in self.tasks:
            if not task.done():
                task.cancel()
                
        # Wait for tasks to complete
        if self.tasks:
            await asyncio.gather(*self.tasks, return_exceptions=True)
            
        self.running = False
        
    def _setup_signal_handlers(self) -> None:
        """Set up signal handlers."""
        loop = asyncio.get_event_loop()
        
        for sig in (signal.SIGINT, signal.SIGTERM):
            loop.add_signal_handler(
                sig,
                lambda: asyncio.create_task(self.shutdown())
            )
