"""
Worker implementation for distributed crawling.
"""
import asyncio
import logging
import os
import platform
import socket
import time
import uuid
from datetime import datetime
from typing import Dict, List, Optional, Any, Union, Callable, Awaitable

import psutil

from .models import WorkerTask, TaskResult, WorkerStatus, WorkerInfo, WorkerHeartbeat
from ...backends.selector import BackendSelector
from ...backends.base import CrawlerBackend

logger = logging.getLogger(__name__)

class CrawlWorker:
    """
    Worker for distributed crawling.
    Handles crawling tasks assigned by the manager.
    """
    
    def __init__(self, 
                 worker_id: Optional[str] = None,
                 backend_selector: Optional[BackendSelector] = None,
                 task_callback: Optional[Callable[[TaskResult], Awaitable[None]]] = None,
                 heartbeat_callback: Optional[Callable[[WorkerHeartbeat], Awaitable[None]]] = None):
        """
        Initialize the worker.
        
        Args:
            worker_id: Optional worker ID (generated if not provided)
            backend_selector: Optional backend selector
            task_callback: Optional callback for task results
            heartbeat_callback: Optional callback for heartbeats
        """
        self.worker_id = worker_id or str(uuid.uuid4())
        self.backend_selector = backend_selector or BackendSelector()
        self.task_callback = task_callback
        self.heartbeat_callback = heartbeat_callback
        
        self.current_task: Optional[WorkerTask] = None
        self.status = WorkerStatus.IDLE
        self.tasks_completed = 0
        self.tasks_failed = 0
        self.start_time = time.time()
        
        # Get worker info
        self.hostname = socket.gethostname()
        self.ip_address = socket.gethostbyname(self.hostname)
        
        # Initialize backends
        self.backends: Dict[str, CrawlerBackend] = {}
        
        logger.info(f"Worker {self.worker_id} initialized on {self.hostname} ({self.ip_address})")
        
    def get_info(self) -> WorkerInfo:
        """
        Get worker information.
        
        Returns:
            WorkerInfo object
        """
        # Get system metrics
        cpu_usage = psutil.cpu_percent(interval=0.1) / 100.0
        memory_usage = psutil.virtual_memory().percent / 100.0
        
        return WorkerInfo(
            worker_id=self.worker_id,
            hostname=self.hostname,
            ip_address=self.ip_address,
            status=self.status,
            current_task_id=self.current_task.task_id if self.current_task else None,
            tasks_completed=self.tasks_completed,
            tasks_failed=self.tasks_failed,
            uptime=time.time() - self.start_time,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            last_heartbeat=datetime.now(),
            capabilities={
                "os": platform.system(),
                "python_version": platform.python_version(),
                "backends": list(self.backends.keys()),
                "cpu_count": os.cpu_count() or 1,
                "memory_total": psutil.virtual_memory().total
            }
        )
        
    async def send_heartbeat(self) -> None:
        """Send a heartbeat to the manager."""
        if not self.heartbeat_callback:
            return
            
        # Get system metrics
        cpu_usage = psutil.cpu_percent(interval=0.1) / 100.0
        memory_usage = psutil.virtual_memory().percent / 100.0
        
        # Create heartbeat
        heartbeat = WorkerHeartbeat(
            worker_id=self.worker_id,
            timestamp=datetime.now(),
            status=self.status,
            current_task_id=self.current_task.task_id if self.current_task else None,
            cpu_usage=cpu_usage,
            memory_usage=memory_usage
        )
        
        # Send heartbeat
        try:
            await self.heartbeat_callback(heartbeat)
        except Exception as e:
            logger.error(f"Error sending heartbeat: {e}")
            
    async def register_backend(self, backend: CrawlerBackend) -> None:
        """
        Register a backend with the worker.
        
        Args:
            backend: Backend to register
        """
        self.backends[backend.name] = backend
        logger.info(f"Registered backend {backend.name} with worker {self.worker_id}")
        
    async def process_task(self, task: WorkerTask) -> TaskResult:
        """
        Process a crawl task.
        
        Args:
            task: Task to process
            
        Returns:
            Task result
        """
        # Update worker status
        self.current_task = task
        self.status = WorkerStatus.BUSY
        task.status = "running"
        task.started_at = datetime.now()
        task.worker_id = self.worker_id
        
        logger.info(f"Worker {self.worker_id} processing task {task.task_id} for URL {task.url}")
        
        # Create result
        result = TaskResult(
            task_id=task.task_id,
            worker_id=self.worker_id,
            url=task.url,
            success=False
        )
        
        start_time = time.time()
        
        try:
            # Select backend
            backend = None
            if task.backend_name and task.backend_name in self.backends:
                backend = self.backends[task.backend_name]
            else:
                backend = self.backend_selector.select_backend_for_url(task.url)
                
            if not backend:
                raise ValueError(f"No suitable backend found for URL {task.url}")
                
            # Crawl URL
            crawl_results = await backend.crawl(task.url, max_depth=task.max_depth)
            
            # Process results
            result.success = True
            result.crawl_time = time.time() - start_time
            result.content_size = sum(len(str(r.content)) for r in crawl_results)
            result.links_found = sum(len(r.links) for r in crawl_results)
            result.content_type = crawl_results[0].content_type if crawl_results else None
            
            # Create child tasks for links if max_depth > 1
            if task.max_depth > 1:
                for crawl_result in crawl_results:
                    for link in crawl_result.links:
                        # Create child task
                        child_task = WorkerTask(
                            url=link,
                            max_depth=task.max_depth - 1,
                            backend_name=task.backend_name,
                            priority=task.priority - 1,
                            parent_task_id=task.task_id
                        )
                        result.child_tasks.append(child_task)
                        
            # Store result data
            result.result_data = {
                "results": [r.model_dump() for r in crawl_results]
            }
            
            # Update task completion stats
            self.tasks_completed += 1
            
        except Exception as e:
            # Handle error
            logger.error(f"Error processing task {task.task_id}: {str(e)}")
            result.success = False
            result.error_message = str(e)
            self.tasks_failed += 1
            
        finally:
            # Update task status
            task.status = "completed" if result.success else "failed"
            task.completed_at = datetime.now()
            
            # Reset worker status
            self.current_task = None
            self.status = WorkerStatus.IDLE
            
            # Send result to callback if available
            if self.task_callback:
                try:
                    await self.task_callback(result)
                except Exception as e:
                    logger.error(f"Error sending task result: {e}")
                    
            return result
            
    async def run_heartbeat_loop(self, interval: int = 10) -> None:
        """
        Run the heartbeat loop.
        
        Args:
            interval: Heartbeat interval in seconds
        """
        while True:
            await self.send_heartbeat()
            await asyncio.sleep(interval)
            
    async def shutdown(self) -> None:
        """Shutdown the worker."""
        logger.info(f"Shutting down worker {self.worker_id}")
        
        # Close backends
        for backend_name, backend in self.backends.items():
            try:
                await backend.close()
            except Exception as e:
                logger.error(f"Error closing backend {backend_name}: {e}")
                
        # Send final heartbeat
        self.status = WorkerStatus.OFFLINE
        await self.send_heartbeat()
