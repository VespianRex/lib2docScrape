"""
Manager implementation for distributed crawling.
"""

import asyncio
import heapq
import logging
import time
from collections import deque
from datetime import datetime
from typing import Optional

from .models import (
    DistributedConfig,
    ManagerStatus,
    TaskResult,
    TaskStatus,
    WorkerHeartbeat,
    WorkerInfo,
    WorkerStatus,
    WorkerTask,
)

logger = logging.getLogger(__name__)


class DistributedCrawlManager:
    """
    Manager for distributed crawling.
    Coordinates workers and distributes tasks.
    """

    def __init__(self, config: Optional[DistributedConfig] = None):
        """
        Initialize the manager.

        Args:
            config: Optional configuration
        """
        self.config = config or DistributedConfig()

        # Task queues
        self.task_queue: list[tuple[int, WorkerTask]] = []  # Priority queue
        self.running_tasks: dict[str, WorkerTask] = {}
        self.completed_tasks: dict[str, TaskResult] = {}
        self.failed_tasks: dict[str, TaskResult] = {}

        # Worker management
        self.workers: dict[str, WorkerInfo] = {}
        self.worker_tasks: dict[str, set[str]] = {}  # worker_id -> set of task_ids

        # Statistics
        self.start_time = time.time()
        self.task_times: deque = deque(maxlen=100)  # Last 100 task times

        logger.info(
            f"Distributed crawl manager initialized with max_workers={self.config.max_workers}"
        )

    def get_status(self) -> ManagerStatus:
        """
        Get manager status.

        Returns:
            ManagerStatus object
        """
        # Count workers by status
        active_workers = sum(
            1 for w in self.workers.values() if w.status == WorkerStatus.BUSY
        )
        idle_workers = sum(
            1 for w in self.workers.values() if w.status == WorkerStatus.IDLE
        )

        # Count tasks by status
        pending_tasks = len(self.task_queue)
        running_tasks = len(self.running_tasks)
        completed_tasks = len(self.completed_tasks)
        failed_tasks = len(self.failed_tasks)
        total_tasks = pending_tasks + running_tasks + completed_tasks + failed_tasks

        # Calculate metrics
        uptime = time.time() - self.start_time
        task_throughput = completed_tasks / uptime if uptime > 0 else 0
        average_task_time = (
            sum(self.task_times) / len(self.task_times) if self.task_times else 0
        )

        return ManagerStatus(
            active_workers=active_workers,
            idle_workers=idle_workers,
            pending_tasks=pending_tasks,
            running_tasks=running_tasks,
            completed_tasks=completed_tasks,
            failed_tasks=failed_tasks,
            total_tasks=total_tasks,
            start_time=datetime.fromtimestamp(self.start_time),
            uptime=uptime,
            task_throughput=task_throughput,
            average_task_time=average_task_time,
        )

    async def register_worker(self, worker_info: WorkerInfo) -> None:
        """
        Register a worker with the manager.

        Args:
            worker_info: Worker information
        """
        worker_id = worker_info.worker_id

        if worker_id in self.workers:
            logger.warning(
                f"Worker {worker_id} already registered, updating information"
            )
        else:
            logger.info(f"Registering worker {worker_id} ({worker_info.hostname})")
            self.worker_tasks[worker_id] = set()

        self.workers[worker_id] = worker_info

    async def unregister_worker(self, worker_id: str) -> None:
        """
        Unregister a worker from the manager.

        Args:
            worker_id: Worker ID
        """
        if worker_id not in self.workers:
            logger.warning(f"Worker {worker_id} not registered")
            return

        logger.info(f"Unregistering worker {worker_id}")

        # Get worker tasks
        task_ids = self.worker_tasks.get(worker_id, set())

        # Requeue running tasks
        for task_id in task_ids:
            if task_id in self.running_tasks:
                task = self.running_tasks.pop(task_id)
                task.status = TaskStatus.PENDING
                task.worker_id = None
                self.add_task(task)
                logger.info(f"Requeued task {task_id} from worker {worker_id}")

        # Remove worker
        del self.workers[worker_id]
        if worker_id in self.worker_tasks:
            del self.worker_tasks[worker_id]

    async def update_worker_heartbeat(self, heartbeat: WorkerHeartbeat) -> None:
        """
        Update worker heartbeat.

        Args:
            heartbeat: Worker heartbeat
        """
        worker_id = heartbeat.worker_id

        if worker_id not in self.workers:
            logger.warning(f"Heartbeat from unknown worker {worker_id}")
            return

        # Update worker info
        worker_info = self.workers[worker_id]
        worker_info.status = heartbeat.status
        worker_info.current_task_id = heartbeat.current_task_id
        worker_info.cpu_usage = heartbeat.cpu_usage
        worker_info.memory_usage = heartbeat.memory_usage
        worker_info.last_heartbeat = heartbeat.timestamp

    def add_task(self, task: WorkerTask) -> None:
        """
        Add a task to the queue.

        Args:
            task: Task to add
        """
        # Check if task queue is full
        if len(self.task_queue) >= self.config.task_queue_limit:
            raise ValueError(
                f"Task queue is full (limit: {self.config.task_queue_limit})"
            )

        # Add task to priority queue
        heapq.heappush(self.task_queue, (-task.priority, task))
        logger.info(f"Added task {task.task_id} to queue (priority: {task.priority})")

    async def get_next_task(self) -> Optional[WorkerTask]:
        """
        Get the next task from the queue.

        Returns:
            Next task or None if queue is empty
        """
        if not self.task_queue:
            return None

        # Get highest priority task
        _, task = heapq.heappop(self.task_queue)
        return task

    async def assign_task(self, worker_id: str, task: WorkerTask) -> None:
        """
        Assign a task to a worker.

        Args:
            worker_id: Worker ID
            task: Task to assign
        """
        if worker_id not in self.workers:
            raise ValueError(f"Worker {worker_id} not registered")

        # Update task
        task.worker_id = worker_id
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()

        # Update worker
        self.workers[worker_id].status = WorkerStatus.BUSY
        self.workers[worker_id].current_task_id = task.task_id

        # Track task
        self.running_tasks[task.task_id] = task
        self.worker_tasks[worker_id].add(task.task_id)

        logger.info(f"Assigned task {task.task_id} to worker {worker_id}")

    async def complete_task(self, result: TaskResult) -> None:
        """
        Complete a task.

        Args:
            result: Task result
        """
        task_id = result.task_id
        worker_id = result.worker_id

        if task_id not in self.running_tasks:
            logger.warning(f"Task {task_id} not found in running tasks")
            return

        # Get task
        task = self.running_tasks.pop(task_id)

        # Update task
        task.status = TaskStatus.COMPLETED if result.success else TaskStatus.FAILED
        task.completed_at = datetime.now()

        # Update worker
        if worker_id in self.workers:
            self.workers[worker_id].status = WorkerStatus.IDLE
            self.workers[worker_id].current_task_id = None
            if worker_id in self.worker_tasks:
                self.worker_tasks[worker_id].discard(task_id)

        # Store result
        if result.success:
            self.completed_tasks[task_id] = result

            # Add child tasks to queue
            for child_task in result.child_tasks:
                self.add_task(child_task)

            # Update statistics
            if task.started_at and task.completed_at:
                task_time = (task.completed_at - task.started_at).total_seconds()
                self.task_times.append(task_time)
        else:
            self.failed_tasks[task_id] = result

        logger.info(f"Task {task_id} {'completed' if result.success else 'failed'}")

    async def find_idle_worker(self) -> Optional[str]:
        """
        Find an idle worker.

        Returns:
            Worker ID or None if no idle workers
        """
        for worker_id, worker_info in self.workers.items():
            if worker_info.status == WorkerStatus.IDLE:
                return worker_id

        return None

    async def check_worker_timeouts(self) -> None:
        """Check for worker timeouts."""
        now = datetime.now()
        timeout_threshold = self.config.worker_idle_timeout

        for worker_id, worker_info in list(self.workers.items()):
            # Check if worker has timed out
            last_heartbeat = worker_info.last_heartbeat
            seconds_since_heartbeat = (now - last_heartbeat).total_seconds()

            if seconds_since_heartbeat > timeout_threshold:
                logger.warning(
                    f"Worker {worker_id} timed out (last heartbeat: {seconds_since_heartbeat:.1f}s ago)"
                )
                await self.unregister_worker(worker_id)

    async def run_task_assignment_loop(self) -> None:
        """Run the task assignment loop."""
        while True:
            try:
                # Check for worker timeouts
                await self.check_worker_timeouts()

                # Find idle worker
                worker_id = await self.find_idle_worker()
                if not worker_id:
                    # No idle workers, wait and try again
                    await asyncio.sleep(1)
                    continue

                # Get next task
                task = await self.get_next_task()
                if not task:
                    # No tasks, wait and try again
                    await asyncio.sleep(1)
                    continue

                # Assign task to worker
                await self.assign_task(worker_id, task)

            except Exception as e:
                logger.error(f"Error in task assignment loop: {e}")
                await asyncio.sleep(1)

    async def run_metrics_loop(self) -> None:
        """Run the metrics loop."""
        if not self.config.metrics_enabled:
            return

        while True:
            try:
                # Log metrics
                status = self.get_status()
                logger.info(
                    f"Manager metrics: workers={status.active_workers}/{status.idle_workers}, "
                    f"tasks={status.pending_tasks}/{status.running_tasks}/{status.completed_tasks}/{status.failed_tasks}, "
                    f"throughput={status.task_throughput:.2f} tasks/s, "
                    f"avg_time={status.average_task_time:.2f}s"
                )

                # Wait for next interval
                await asyncio.sleep(self.config.metrics_interval)

            except Exception as e:
                logger.error(f"Error in metrics loop: {e}")
                await asyncio.sleep(self.config.metrics_interval)

    async def run(self) -> None:
        """Run the manager."""
        logger.info("Starting distributed crawl manager")

        # Start task assignment loop
        task_assignment_task = asyncio.create_task(self.run_task_assignment_loop())

        # Start metrics loop
        metrics_task = asyncio.create_task(self.run_metrics_loop())

        try:
            # Wait for tasks to complete
            await asyncio.gather(task_assignment_task, metrics_task)
        except asyncio.CancelledError:
            logger.info("Manager tasks cancelled")
        finally:
            # Cancel tasks
            task_assignment_task.cancel()
            metrics_task.cancel()

            logger.info("Distributed crawl manager stopped")
