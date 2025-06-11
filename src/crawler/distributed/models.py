"""
Models for distributed crawling.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field, validator


class TaskStatus(str, Enum):
    """Status of a crawl task."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


class WorkerStatus(str, Enum):
    """Status of a crawl worker."""

    IDLE = "idle"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"


class DistributedConfig(BaseModel):
    """Configuration for distributed crawling."""

    max_workers: int = 5
    task_timeout: int = 300  # seconds
    retry_count: int = 3
    retry_delay: int = 5  # seconds
    heartbeat_interval: int = 10  # seconds
    result_batch_size: int = 10
    worker_idle_timeout: int = 60  # seconds
    enable_load_balancing: bool = True
    enable_task_prioritization: bool = True
    enable_worker_auto_scaling: bool = False
    min_workers: int = 1
    max_worker_tasks: int = 100
    worker_memory_limit: int = 512  # MB
    worker_cpu_limit: float = 1.0  # cores
    task_queue_limit: int = 1000
    result_queue_limit: int = 1000
    log_level: str = "INFO"
    metrics_enabled: bool = True
    metrics_interval: int = 30  # seconds


class WorkerTask(BaseModel):
    """Model for a crawl task assigned to a worker."""

    task_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    url: str
    max_depth: int = 1
    backend_name: Optional[str] = None
    priority: int = 0
    created_at: datetime = Field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: TaskStatus = TaskStatus.PENDING
    worker_id: Optional[str] = None
    retry_count: int = 0
    parent_task_id: Optional[str] = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @validator("url")
    def validate_url(cls, v):
        """Validate URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("URL must start with http:// or https://")
        return v


class TaskResult(BaseModel):
    """Model for a crawl task result."""

    task_id: str
    worker_id: str
    url: str
    success: bool
    error_message: Optional[str] = None
    crawl_time: float = 0.0
    content_size: int = 0
    links_found: int = 0
    status_code: Optional[int] = None
    content_type: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.now)
    metadata: dict[str, Any] = Field(default_factory=dict)
    result_data: Optional[dict[str, Any]] = None
    child_tasks: list[WorkerTask] = Field(default_factory=list)


class WorkerInfo(BaseModel):
    """Model for worker information."""

    worker_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    hostname: str
    ip_address: str
    status: WorkerStatus = WorkerStatus.IDLE
    current_task_id: Optional[str] = None
    tasks_completed: int = 0
    tasks_failed: int = 0
    uptime: float = 0.0
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    last_heartbeat: datetime = Field(default_factory=datetime.now)
    capabilities: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)


class WorkerHeartbeat(BaseModel):
    """Model for worker heartbeat."""

    worker_id: str
    timestamp: datetime = Field(default_factory=datetime.now)
    status: WorkerStatus
    current_task_id: Optional[str] = None
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class ManagerStatus(BaseModel):
    """Model for manager status."""

    active_workers: int = 0
    idle_workers: int = 0
    pending_tasks: int = 0
    running_tasks: int = 0
    completed_tasks: int = 0
    failed_tasks: int = 0
    canceled_tasks: int = 0
    total_tasks: int = 0
    start_time: datetime = Field(default_factory=datetime.now)
    uptime: float = 0.0
    task_throughput: float = 0.0  # tasks per second
    average_task_time: float = 0.0  # seconds
    metadata: dict[str, Any] = Field(default_factory=dict)
