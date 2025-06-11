"""
Tests for distributed crawling.
"""

from unittest.mock import AsyncMock

import pytest

from src.backends.base import CrawlerBackend, CrawlResult
from src.crawler.distributed.manager import DistributedCrawlManager
from src.crawler.distributed.models import (
    DistributedConfig,
    TaskResult,
    TaskStatus,
    WorkerInfo,
    WorkerStatus,
    WorkerTask,
)
from src.crawler.distributed.worker import CrawlWorker


class MockBackend(CrawlerBackend):
    """Mock backend for testing."""

    def __init__(self, name="mock_backend"):
        super().__init__(name=name)
        self._crawl_mock = AsyncMock()
        self._validate_mock = AsyncMock(return_value=True)
        self._process_mock = AsyncMock(return_value={})
        self._close_mock = AsyncMock()

    async def crawl(self, url_info, max_depth=1, config=None):
        """Mock implementation of crawl method."""
        result = self._crawl_mock(url_info, config)

        # Convert the result to a CrawlResult if it's not already one
        if not isinstance(result, CrawlResult):
            if (
                isinstance(result, list)
                and result
                and isinstance(result[0], CrawlResult)
            ):
                # If we get a list of CrawlResults, use it
                return result
            else:
                # Create a default CrawlResult
                result = CrawlResult(
                    url="https://example.com",
                    content={"html": "Example content"},
                    metadata={},
                    status=200,
                    content_type="text/html",
                )

        # Create a wrapper class that provides the links and model_dump we need
        class CrawlResultWrapper:
            def __init__(self, crawl_result):
                self.url = crawl_result.url
                self.content = crawl_result.content
                self.metadata = crawl_result.metadata
                self.status = crawl_result.status
                self.error = getattr(crawl_result, "error", None)
                self.content_type = getattr(crawl_result, "content_type", None)
                self.links = ["https://example.com/link1", "https://example.com/link2"]

            def model_dump(self):
                return {
                    "url": self.url,
                    "content": self.content,
                    "metadata": self.metadata,
                    "status": self.status,
                    "content_type": self.content_type,
                    "links": self.links,
                }

        # Create a wrapped version of the result with links
        wrapped_result = CrawlResultWrapper(result)

        # Always return a list of our wrapped results
        return [wrapped_result]

    async def validate(self, content):
        """Mock implementation of validate method."""
        return self._validate_mock(content)

    async def process(self, content):
        """Mock implementation of process method."""
        return self._process_mock(content)

    async def close(self):
        """Mock implementation of close method."""
        return self._close_mock()


@pytest.fixture
def mock_backend():
    """Create a mock backend for testing."""
    backend = MockBackend()
    # Set up crawl to return a CrawlResult object
    backend._crawl_mock.return_value = CrawlResult(
        url="https://example.com",
        content={"html": "Example content"},
        metadata={},
        status=200,
        content_type="text/html",
    )
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
        metrics_enabled=False,
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
        backend_name=mock_backend.name,
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

    # Check that backend's crawl method was called with the right URL and config
    mock_backend._crawl_mock.assert_called_once()


@pytest.mark.asyncio
async def test_worker_process_task_error(worker):
    """Test processing a task with an error."""
    # Create task with invalid backend
    task = WorkerTask(
        task_id="test_task",
        url="https://example.com",
        max_depth=1,
        backend_name="nonexistent_backend",
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
        status=WorkerStatus.IDLE,
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
        task_id="test_task", url="https://example.com", max_depth=1, priority=10
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
        status=WorkerStatus.IDLE,
    )
    await manager.register_worker(worker_info)

    # Create task
    task = WorkerTask(task_id="test_task", url="https://example.com", max_depth=1)

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
        status=WorkerStatus.IDLE,
    )
    await manager.register_worker(worker_info)

    # Create and assign task
    task = WorkerTask(task_id="test_task", url="https://example.com", max_depth=1)
    await manager.assign_task("test_worker", task)

    # Create result
    result = TaskResult(
        task_id=task.task_id,
        worker_id="test_worker",
        url=task.url,
        success=True,
        crawl_time=1.0,
        content_size=1000,
        links_found=5,
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
        status=WorkerStatus.IDLE,
    )
    await manager.register_worker(worker_info)

    # Create and assign task
    task = WorkerTask(task_id="test_task", url="https://example.com", max_depth=1)
    await manager.assign_task("test_worker", task)

    # Create result with failure
    result = TaskResult(
        task_id=task.task_id,
        worker_id="test_worker",
        url=task.url,
        success=False,
        error_message="Test error",
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
        status=WorkerStatus.IDLE,
    )
    worker2 = WorkerInfo(
        worker_id="worker2",
        hostname="host2",
        ip_address="127.0.0.2",
        status=WorkerStatus.BUSY,
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
