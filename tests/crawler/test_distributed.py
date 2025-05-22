"""
Tests for distributed crawling.
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.crawler.distributed.models import (
    WorkerTask, TaskResult, WorkerStatus, WorkerInfo, WorkerHeartbeat,
    DistributedConfig, TaskStatus
)
from src.crawler.distributed.worker import CrawlWorker
from src.crawler.distributed.manager import DistributedCrawlManager
from src.backends.base import CrawlerBackend, CrawlResult

class MockBackend(CrawlerBackend):
    """Mock backend for testing."""
    
    def __init__(self, name="mock_backend"):
        super().__init__(name=name)
        self.crawl = AsyncMock()
        self.validate = AsyncMock(return_value=True)
        self.process = AsyncMock(return_value={})
        self.close = AsyncMock()

@pytest.fixture
def mock_backend():
    """Create a mock backend for testing."""
    backend = MockBackend()
    # Set up crawl to return a list of CrawlResult objects
    backend.crawl.return_value = [
        CrawlResult(
            url="https://example.com",
            content="Example content",
            content_type="text/html",
            links=["https://example.com/page1", "https://example.com/page2"]
        )
    ]
    return backend

@pytest.fixture
def worker(mock_backend):
    """Create a worker for testing."""
    worker = CrawlWorker(worker_id="test_worker")
    return worker

@pytest.fixture
def manager():
    """Create a manager for testing."""
    config = DistributedConfig(
        max_workers=2,
        task_timeout=10,
        retry_count=1,
        heartbeat_interval=1,
        metrics_enabled=False
    )
    return DistributedCrawlManager(config=config)

@pytest.mark.asyncio
async def test_worker_initialization():
    """Test worker initialization."""
    worker = CrawlWorker(worker_id="test_worker")
    
    assert worker.worker_id == "test_worker"
    assert worker.status == WorkerStatus.IDLE
    assert worker.tasks_completed == 0
    assert worker.tasks_failed == 0
    assert worker.current_task is None

@pytest.mark.asyncio
async def test_worker_register_backend(worker, mock_backend):
    """Test registering a backend with a worker."""
    await worker.register_backend(mock_backend)
    
    assert mock_backend.name in worker.backends
    assert worker.backends[mock_backend.name] == mock_backend

@pytest.mark.asyncio
async def test_worker_process_task(worker, mock_backend):
    """Test processing a task."""
    # Register backend
    await worker.register_backend(mock_backend)
    
    # Create task
    task = WorkerTask(
        task_id="test_task",
        url="https://example.com",
        max_depth=1,
        backend_name=mock_backend.name
    )
    
    # Process task
    result = await worker.process_task(task)
    
    # Check result
    assert result.task_id == task.task_id
    assert result.worker_id == worker.worker_id
    assert result.url == task.url
    assert result.success is True
    assert result.links_found == 2
    assert worker.tasks_completed == 1
    assert worker.tasks_failed == 0
    assert worker.status == WorkerStatus.IDLE
    assert worker.current_task is None
    
    # Check that backend was called
    mock_backend.crawl.assert_called_once_with(task.url, max_depth=task.max_depth)

@pytest.mark.asyncio
async def test_worker_process_task_error(worker):
    """Test processing a task with an error."""
    # Create task with invalid backend
    task = WorkerTask(
        task_id="test_task",
        url="https://example.com",
        max_depth=1,
        backend_name="nonexistent_backend"
    )
    
    # Process task
    result = await worker.process_task(task)
    
    # Check result
    assert result.task_id == task.task_id
    assert result.worker_id == worker.worker_id
    assert result.url == task.url
    assert result.success is False
    assert result.error_message is not None
    assert worker.tasks_completed == 0
    assert worker.tasks_failed == 1
    assert worker.status == WorkerStatus.IDLE
    assert worker.current_task is None

@pytest.mark.asyncio
async def test_worker_get_info(worker):
    """Test getting worker information."""
    info = worker.get_info()
    
    assert info.worker_id == worker.worker_id
    assert info.hostname == worker.hostname
    assert info.ip_address == worker.ip_address
    assert info.status == WorkerStatus.IDLE
    assert info.current_task_id is None
    assert info.tasks_completed == 0
    assert info.tasks_failed == 0
    assert info.uptime >= 0
    assert info.cpu_usage >= 0
    assert info.memory_usage >= 0

@pytest.mark.asyncio
async def test_manager_initialization():
    """Test manager initialization."""
    config = DistributedConfig(max_workers=5)
    manager = DistributedCrawlManager(config=config)
    
    assert manager.config.max_workers == 5
    assert len(manager.task_queue) == 0
    assert len(manager.running_tasks) == 0
    assert len(manager.completed_tasks) == 0
    assert len(manager.failed_tasks) == 0
    assert len(manager.workers) == 0
    assert len(manager.worker_tasks) == 0

@pytest.mark.asyncio
async def test_manager_register_worker(manager):
    """Test registering a worker with the manager."""
    # Create worker info
    worker_info = WorkerInfo(
        worker_id="test_worker",
        hostname="test_host",
        ip_address="127.0.0.1",
        status=WorkerStatus.IDLE
    )
    
    # Register worker
    await manager.register_worker(worker_info)
    
    # Check that worker was registered
    assert "test_worker" in manager.workers
    assert manager.workers["test_worker"] == worker_info
    assert "test_worker" in manager.worker_tasks
    assert len(manager.worker_tasks["test_worker"]) == 0

@pytest.mark.asyncio
async def test_manager_add_task(manager):
    """Test adding a task to the manager."""
    # Create task
    task = WorkerTask(
        task_id="test_task",
        url="https://example.com",
        max_depth=1,
        priority=10
    )
    
    # Add task
    manager.add_task(task)
    
    # Check that task was added to queue
    assert len(manager.task_queue) == 1
    
    # Get next task
    next_task = await manager.get_next_task()
    
    # Check that task was retrieved
    assert next_task.task_id == task.task_id
    assert next_task.url == task.url
    assert next_task.max_depth == task.max_depth
    assert next_task.priority == task.priority

@pytest.mark.asyncio
async def test_manager_assign_task(manager):
    """Test assigning a task to a worker."""
    # Register worker
    worker_info = WorkerInfo(
        worker_id="test_worker",
        hostname="test_host",
        ip_address="127.0.0.1",
        status=WorkerStatus.IDLE
    )
    await manager.register_worker(worker_info)
    
    # Create task
    task = WorkerTask(
        task_id="test_task",
        url="https://example.com",
        max_depth=1
    )
    
    # Assign task
    await manager.assign_task("test_worker", task)
    
    # Check that task was assigned
    assert task.worker_id == "test_worker"
    assert task.status == TaskStatus.RUNNING
    assert task.started_at is not None
    
    # Check that worker was updated
    assert manager.workers["test_worker"].status == WorkerStatus.BUSY
    assert manager.workers["test_worker"].current_task_id == task.task_id
    
    # Check that task is tracked
    assert task.task_id in manager.running_tasks
    assert task.task_id in manager.worker_tasks["test_worker"]

@pytest.mark.asyncio
async def test_manager_complete_task(manager):
    """Test completing a task."""
    # Register worker
    worker_info = WorkerInfo(
        worker_id="test_worker",
        hostname="test_host",
        ip_address="127.0.0.1",
        status=WorkerStatus.IDLE
    )
    await manager.register_worker(worker_info)
    
    # Create and assign task
    task = WorkerTask(
        task_id="test_task",
        url="https://example.com",
        max_depth=1
    )
    await manager.assign_task("test_worker", task)
    
    # Create result
    result = TaskResult(
        task_id=task.task_id,
        worker_id="test_worker",
        url=task.url,
        success=True,
        crawl_time=1.0,
        content_size=1000,
        links_found=5
    )
    
    # Complete task
    await manager.complete_task(result)
    
    # Check that task was completed
    assert task.task_id not in manager.running_tasks
    assert task.task_id in manager.completed_tasks
    assert manager.completed_tasks[task.task_id] == result
    
    # Check that worker was updated
    assert manager.workers["test_worker"].status == WorkerStatus.IDLE
    assert manager.workers["test_worker"].current_task_id is None
    assert task.task_id not in manager.worker_tasks["test_worker"]

@pytest.mark.asyncio
async def test_manager_complete_task_failure(manager):
    """Test completing a task with failure."""
    # Register worker
    worker_info = WorkerInfo(
        worker_id="test_worker",
        hostname="test_host",
        ip_address="127.0.0.1",
        status=WorkerStatus.IDLE
    )
    await manager.register_worker(worker_info)
    
    # Create and assign task
    task = WorkerTask(
        task_id="test_task",
        url="https://example.com",
        max_depth=1
    )
    await manager.assign_task("test_worker", task)
    
    # Create result with failure
    result = TaskResult(
        task_id=task.task_id,
        worker_id="test_worker",
        url=task.url,
        success=False,
        error_message="Test error"
    )
    
    # Complete task
    await manager.complete_task(result)
    
    # Check that task was failed
    assert task.task_id not in manager.running_tasks
    assert task.task_id not in manager.completed_tasks
    assert task.task_id in manager.failed_tasks
    assert manager.failed_tasks[task.task_id] == result
    
    # Check that worker was updated
    assert manager.workers["test_worker"].status == WorkerStatus.IDLE
    assert manager.workers["test_worker"].current_task_id is None
    assert task.task_id not in manager.worker_tasks["test_worker"]

@pytest.mark.asyncio
async def test_manager_find_idle_worker(manager):
    """Test finding an idle worker."""
    # Register workers
    worker1 = WorkerInfo(
        worker_id="worker1",
        hostname="host1",
        ip_address="127.0.0.1",
        status=WorkerStatus.IDLE
    )
    worker2 = WorkerInfo(
        worker_id="worker2",
        hostname="host2",
        ip_address="127.0.0.2",
        status=WorkerStatus.BUSY
    )
    
    await manager.register_worker(worker1)
    await manager.register_worker(worker2)
    
    # Find idle worker
    idle_worker = await manager.find_idle_worker()
    
    # Check that worker1 was found
    assert idle_worker == "worker1"
    
    # Make worker1 busy
    manager.workers["worker1"].status = WorkerStatus.BUSY
    
    # Find idle worker again
    idle_worker = await manager.find_idle_worker()
    
    # Check that no idle worker was found
    assert idle_worker is None
