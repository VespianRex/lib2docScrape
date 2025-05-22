import pytest
from datetime import datetime, timedelta
import uuid

# Pydantic v1/v2 compatibility
try:
    from pydantic.v1 import ValidationError
except ImportError:
    from pydantic import ValidationError

from src.crawler.distributed.models import (
    TaskStatus,
    WorkerStatus,
    DistributedConfig,
    WorkerTask,
    TaskResult,
    WorkerInfo,
    WorkerHeartbeat,
    ManagerStatus
)

def test_task_status_enum():
    assert TaskStatus.PENDING == "pending"
    assert TaskStatus.RUNNING == "running"
    assert TaskStatus.COMPLETED == "completed"
    assert TaskStatus.FAILED == "failed"
    assert TaskStatus.CANCELED == "canceled"
    with pytest.raises(AttributeError): # Or check __members__
        TaskStatus.UNKNOWN 

def test_worker_status_enum():
    assert WorkerStatus.IDLE == "idle"
    assert WorkerStatus.BUSY == "busy"
    assert WorkerStatus.OFFLINE == "offline"
    assert WorkerStatus.ERROR == "error"

def test_distributed_config_defaults():
    config = DistributedConfig()
    assert config.max_workers == 5
    assert config.task_timeout == 300
    assert config.retry_count == 3
    assert config.heartbeat_interval == 10
    assert config.task_queue_limit == 1000
    assert config.metrics_enabled is True
    assert config.metrics_interval == 30

def test_distributed_config_custom():
    custom_values = {
        "max_workers": 10,
        "task_timeout": 60,
        "metrics_enabled": False
    }
    config = DistributedConfig(**custom_values)
    assert config.max_workers == 10
    assert config.task_timeout == 60
    assert config.metrics_enabled is False

def test_worker_task_defaults():
    url = "http://example.com/task"
    task = WorkerTask(url=url)
    assert isinstance(task.task_id, str)
    assert len(task.task_id) == 36 # UUID length
    assert task.url == url
    assert task.max_depth == 1
    assert task.priority == 0
    assert task.status == TaskStatus.PENDING
    assert isinstance(task.created_at, datetime)
    assert task.retry_count == 0
    assert task.metadata == {}

def test_worker_task_custom():
    uid = str(uuid.uuid4())
    url = "https://example.com/custom"
    created = datetime.now() - timedelta(hours=1)
    task = WorkerTask(
        task_id=uid,
        url=url,
        max_depth=3,
        priority=5,
        created_at=created,
        status=TaskStatus.RUNNING,
        worker_id="worker-1",
        retry_count=1,
        parent_task_id="parent-123",
        metadata={"key": "value"}
    )
    assert task.task_id == uid
    assert task.url == url
    assert task.max_depth == 3
    assert task.priority == 5
    assert task.created_at == created
    assert task.status == TaskStatus.RUNNING
    assert task.worker_id == "worker-1"
    assert task.retry_count == 1
    assert task.parent_task_id == "parent-123"
    assert task.metadata == {"key": "value"}

def test_worker_task_url_validation():
    with pytest.raises(ValidationError):
        WorkerTask(url="ftp://invalid.com")
    with pytest.raises(ValidationError):
        WorkerTask(url="example.com")
    
    task_http = WorkerTask(url="http://example.com")
    assert task_http.url == "http://example.com"
    task_https = WorkerTask(url="https://example.com")
    assert task_https.url == "https://example.com"


def test_task_result_defaults():
    task_id = "task-abc"
    worker_id = "worker-xyz"
    url = "http://example.com/result"
    
    result = TaskResult(task_id=task_id, worker_id=worker_id, url=url, success=True)
    
    assert result.task_id == task_id
    assert result.worker_id == worker_id
    assert result.url == url
    assert result.success is True
    assert result.error_message is None
    assert result.crawl_time == 0.0
    assert result.content_size == 0
    assert result.links_found == 0
    assert result.status_code is None
    assert result.content_type is None
    assert isinstance(result.created_at, datetime)
    assert result.metadata == {}
    assert result.result_data is None
    assert result.child_tasks == []

def test_task_result_custom():
    result = TaskResult(
        task_id="task-001",
        worker_id="worker-A",
        url="https://test.com/page",
        success=False,
        error_message="Timeout",
        crawl_time=1.23,
        content_size=1024,
        links_found=5,
        status_code=504,
        content_type="text/plain",
        metadata={"source": "test"},
        result_data={"raw": "error data"},
        child_tasks=[WorkerTask(url="https://test.com/child1")]
    )
    assert result.success is False
    assert result.error_message == "Timeout"
    assert result.crawl_time == 1.23
    assert len(result.child_tasks) == 1
    assert result.child_tasks[0].url == "https://test.com/child1"

def test_worker_info_defaults():
    hostname = "test-host"
    ip_address = "127.0.0.1"
    info = WorkerInfo(hostname=hostname, ip_address=ip_address)

    assert isinstance(info.worker_id, str)
    assert info.hostname == hostname
    assert info.ip_address == ip_address
    assert info.status == WorkerStatus.IDLE
    assert info.current_task_id is None
    assert info.tasks_completed == 0
    assert info.tasks_failed == 0
    assert info.uptime == 0.0
    assert info.cpu_usage == 0.0
    assert info.memory_usage == 0.0
    assert isinstance(info.last_heartbeat, datetime)
    assert info.capabilities == {}
    assert info.metadata == {}


def test_worker_info_custom():
    last_hb = datetime.now() - timedelta(seconds=30)
    info = WorkerInfo(
        worker_id="custom-worker-id",
        hostname="prod-worker-01",
        ip_address="192.168.1.100",
        status=WorkerStatus.BUSY,
        current_task_id="task-current",
        tasks_completed=10,
        tasks_failed=1,
        uptime=3600.5,
        cpu_usage=0.75,
        memory_usage=0.55,
        last_heartbeat=last_hb,
        capabilities={"gpu": True, "os": "linux"},
        metadata={"region": "us-east"}
    )
    assert info.worker_id == "custom-worker-id"
    assert info.status == WorkerStatus.BUSY
    assert info.current_task_id == "task-current"
    assert info.cpu_usage == 0.75
    assert info.capabilities == {"gpu": True, "os": "linux"}

def test_worker_heartbeat_defaults():
    worker_id = "worker-hb-test"
    status = WorkerStatus.IDLE
    hb = WorkerHeartbeat(worker_id=worker_id, status=status)

    assert hb.worker_id == worker_id
    assert isinstance(hb.timestamp, datetime)
    assert hb.status == status
    assert hb.current_task_id is None
    assert hb.cpu_usage == 0.0
    assert hb.memory_usage == 0.0
    assert hb.metadata == {}

def test_worker_heartbeat_custom():
    ts = datetime.now() - timedelta(seconds=5)
    hb = WorkerHeartbeat(
        worker_id="worker-002",
        timestamp=ts,
        status=WorkerStatus.BUSY,
        current_task_id="task-active-on-worker-002",
        cpu_usage=0.9,
        memory_usage=0.2,
        metadata={"load_avg": 0.8}
    )
    assert hb.timestamp == ts
    assert hb.status == WorkerStatus.BUSY
    assert hb.current_task_id == "task-active-on-worker-002"
    assert hb.cpu_usage == 0.9
    assert hb.metadata == {"load_avg": 0.8}

def test_manager_status_defaults():
    status = ManagerStatus()
    assert status.active_workers == 0
    assert status.idle_workers == 0
    assert status.pending_tasks == 0
    assert status.running_tasks == 0
    assert status.completed_tasks == 0
    assert status.failed_tasks == 0
    assert status.canceled_tasks == 0 # Make sure this field is tested
    assert status.total_tasks == 0
    assert isinstance(status.start_time, datetime)
    assert status.uptime == 0.0
    assert status.task_throughput == 0.0
    assert status.average_task_time == 0.0
    assert status.metadata == {}

def test_manager_status_custom():
    st = datetime.now() - timedelta(minutes=10)
    status = ManagerStatus(
        active_workers=2,
        idle_workers=3,
        pending_tasks=100,
        running_tasks=2,
        completed_tasks=50,
        failed_tasks=5,
        canceled_tasks=1,
        total_tasks=158, # 100+2+50+5+1
        start_time=st,
        uptime=600.0,
        task_throughput=0.0833, # 50 tasks / 600s
        average_task_time=10.5,
        metadata={"cluster_name": "prod"}
    )
    assert status.active_workers == 2
    assert status.total_tasks == 158
    assert status.start_time == st
    assert status.task_throughput == 0.0833
    assert status.average_task_time == 10.5
    assert status.metadata == {"cluster_name": "prod"}