import time
from dataclasses import dataclass
from enum import Enum
from typing import Optional

from fastapi import WebSocket


class TestStatus(Enum):
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    COMPLETED = "completed"


@dataclass
class TestMetrics:
    duration: str
    pass_rate: float
    memory_usage: float
    cpu_usage: float


class TestWebSocketManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
        self.test_status = TestStatus.STOPPED
        self.current_metrics = TestMetrics("00:00:00", 0.0, 0.0, 0.0)
        self.start_time: Optional[float] = None
        self.stats = {"passed": 0, "failed": 0, "skipped": 0, "total": 0}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        await self._send_initial_state(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def _send_initial_state(self, websocket: WebSocket):
        """Send current state to newly connected client"""
        await websocket.send_json(
            {
                "type": "connection_established",
                "data": {
                    "status": self.test_status.value,
                    "metrics": self.__get_metrics_dict(),
                    "stats": self.stats,
                },
            }
        )

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                await self.disconnect(connection)

    async def handle_message(self, _websocket: WebSocket, data: dict):
        """Handle incoming WebSocket messages"""
        message_type = data.get("type")

        if message_type == "control":
            await self._handle_control_message(data)
        elif message_type == "log_filter":
            # Handled client-side, but could add server-side filtering
            pass

    async def _handle_control_message(self, data: dict):
        """Handle test control messages"""
        action = data.get("action")

        if action == "pause" and self.test_status == TestStatus.RUNNING:
            self.test_status = TestStatus.PAUSED
            await self.broadcast({"type": "status", "data": {"status": "paused"}})

        elif action == "resume" and self.test_status == TestStatus.PAUSED:
            self.test_status = TestStatus.RUNNING
            await self.broadcast({"type": "status", "data": {"status": "running"}})

        elif action == "stop":
            self.test_status = TestStatus.STOPPED
            await self.broadcast({"type": "status", "data": {"status": "stopped"}})
            await self._reset_state()

    async def _reset_state(self):
        """Reset test state"""
        self.start_time = None
        self.current_metrics = TestMetrics("00:00:00", 0.0, 0.0, 0.0)
        self.stats = {"passed": 0, "failed": 0, "skipped": 0, "total": 0}
        await self.broadcast(
            {
                "type": "reset",
                "data": {"metrics": self.__get_metrics_dict(), "stats": self.stats},
            }
        )

    def __get_metrics_dict(self) -> dict:
        """Convert metrics to dictionary format"""
        return {
            "duration": self.current_metrics.duration,
            "passRate": self.current_metrics.pass_rate,
            "memoryUsage": self.current_metrics.memory_usage,
            "cpuUsage": self.current_metrics.cpu_usage,
        }

    async def update_progress(self, completed: int, total: int):
        """Update test progress"""
        await self.broadcast(
            {"type": "test_progress", "data": {"completed": completed, "total": total}}
        )

    async def update_status(self, status_update: dict):
        """Update test status counts"""
        self.stats.update(status_update)
        await self.broadcast({"type": "test_status", "data": self.stats})

    async def add_log(self, level: str, message: str):
        """Add a log message"""
        await self.broadcast(
            {
                "type": "log",
                "data": {
                    "level": level,
                    "message": message,
                    "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                },
            }
        )

    async def update_metrics(self, metrics: TestMetrics):
        """Update test metrics"""
        self.current_metrics = metrics
        await self.broadcast({"type": "metrics", "data": self.__get_metrics_dict()})


# Global instance
test_ws_manager = TestWebSocketManager()
