"""
Backend performance tracking system.

This module tracks performance metrics for different backends and provides
automatic backend selection based on resource usage and compute performance.
"""

import json
import logging
import time
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any, Optional

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    PSUTIL_AVAILABLE = False
    logging.warning("psutil not available - memory and CPU monitoring will be limited")

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for a backend operation."""

    response_time: float
    memory_usage: float  # MB
    cpu_usage: float  # %
    success: bool
    content_size: int  # bytes
    timestamp: float


@dataclass
class MonitoringContext:
    """Context for monitoring a backend operation."""

    backend_name: str
    domain: str
    start_time: float
    start_memory: float
    start_cpu: float
    process: Optional[Any] = None


class BackendPerformanceTracker:
    """
    Tracks performance metrics for different backends and provides
    automatic backend selection based on historical performance.
    """

    def __init__(
        self,
        storage_path: Optional[Path] = None,
        max_history_days: int = 30,
        min_samples_for_recommendation: int = 3,
    ):
        """
        Initialize the performance tracker.

        Args:
            storage_path: Path to store performance data
            max_history_days: Maximum days to keep performance history
            min_samples_for_recommendation: Minimum samples needed for recommendations
        """
        self.storage_path = storage_path or Path("backend_performance.json")
        self.max_history_days = max_history_days
        self.min_samples_for_recommendation = min_samples_for_recommendation

        # Performance data structure:
        # {
        #   "domain.com": {
        #     "backend_name": {
        #       "history": [PerformanceMetrics, ...],
        #       "average_response_time": float,
        #       "average_memory_usage": float,
        #       "average_cpu_usage": float,
        #       "success_rate": float,
        #       "total_requests": int,
        #       "last_updated": float
        #     }
        #   }
        # }
        self.domain_performance: dict[str, dict[str, dict[str, Any]]] = {}
        self.performance_data: dict[str, Any] = {}

        # Default backend preference order (fallback)
        self.default_backend_order = [
            "http",
            "crawl4ai",
            "playwright",
            "scrapy",
            "lightpanda",
        ]

    async def record_performance(
        self, backend_name: str, domain: str, metrics: dict[str, Any]
    ) -> None:
        """
        Record performance metrics for a backend on a specific domain.

        Args:
            backend_name: Name of the backend
            domain: Domain that was crawled
            metrics: Performance metrics dictionary
        """
        # Ensure domain exists in tracking
        if domain not in self.domain_performance:
            self.domain_performance[domain] = {}

        # Ensure backend exists for domain
        if backend_name not in self.domain_performance[domain]:
            self.domain_performance[domain][backend_name] = {
                "history": [],
                "average_response_time": 0.0,
                "average_memory_usage": 0.0,
                "average_cpu_usage": 0.0,
                "success_rate": 0.0,
                "total_requests": 0,
                "last_updated": time.time(),
            }

        backend_data = self.domain_performance[domain][backend_name]

        # Add to history
        backend_data["history"].append(metrics)
        backend_data["total_requests"] += 1
        backend_data["last_updated"] = time.time()

        # Update averages
        history = backend_data["history"]
        backend_data["average_response_time"] = mean(
            [m["response_time"] for m in history]
        )
        backend_data["average_memory_usage"] = mean(
            [m["memory_usage"] for m in history]
        )
        backend_data["average_cpu_usage"] = mean([m["cpu_usage"] for m in history])
        backend_data["success_rate"] = mean(
            [1.0 if m["success"] else 0.0 for m in history]
        )

        logger.debug(f"Recorded performance for {backend_name} on {domain}: {metrics}")

    def get_best_backend_for_domain(self, domain: str) -> str:
        """
        Get the best performing backend for a specific domain.

        Args:
            domain: Domain to get recommendation for

        Returns:
            Name of the recommended backend
        """
        if domain not in self.domain_performance:
            # No data for domain, return default
            return self.default_backend_order[0]

        domain_data = self.domain_performance[domain]

        # Filter backends with sufficient data
        candidates = {}
        for backend_name, backend_data in domain_data.items():
            if backend_data["total_requests"] >= self.min_samples_for_recommendation:
                score = self.calculate_performance_score(backend_data)
                candidates[backend_name] = score
                logger.debug(
                    f"Backend {backend_name} score: {score:.3f} (data: {backend_data})"
                )

        if not candidates:
            # No backends with sufficient data, return default
            return self.default_backend_order[0]

        # Return backend with highest score
        best_backend = max(candidates.items(), key=lambda x: x[1])[0]
        logger.info(
            f"Recommended backend for {domain}: {best_backend} (score: {candidates[best_backend]:.3f})"
        )
        logger.debug(f"All candidates: {candidates}")
        return best_backend

    def calculate_performance_score(self, performance_data: dict[str, Any]) -> float:
        """
        Calculate a performance score for a backend.
        Higher score is better.

        Args:
            performance_data: Backend performance data

        Returns:
            Performance score between 0 and 1
        """
        # Weights for different metrics (can be tuned)
        weights = {
            "response_time": 0.4,  # Lower is better
            "memory_usage": 0.3,  # Lower is better
            "cpu_usage": 0.2,  # Lower is better
            "success_rate": 0.1,  # Higher is better
        }

        # Normalize metrics (assuming reasonable ranges)
        response_time_score = max(
            0, 1 - (performance_data["average_response_time"] / 5.0)
        )  # 5s max
        memory_score = max(
            0, 1 - (performance_data["average_memory_usage"] / 200.0)
        )  # 200MB max
        cpu_score = max(
            0, 1 - (performance_data["average_cpu_usage"] / 50.0)
        )  # 50% max
        success_score = performance_data["success_rate"]

        # Calculate weighted score
        score = (
            weights["response_time"] * response_time_score
            + weights["memory_usage"] * memory_score
            + weights["cpu_usage"] * cpu_score
            + weights["success_rate"] * success_score
        )

        return min(1.0, max(0.0, score))

    async def save_performance_data(self) -> None:
        """Save performance data to storage."""
        try:
            # Convert to JSON-serializable format
            data_to_save = {}
            for domain, backends in self.domain_performance.items():
                data_to_save[domain] = {}
                for backend_name, backend_data in backends.items():
                    data_to_save[domain][backend_name] = backend_data.copy()

            with open(self.storage_path, "w") as f:
                json.dump(data_to_save, f, indent=2)

            logger.debug(f"Saved performance data to {self.storage_path}")
        except Exception as e:
            logger.error(f"Failed to save performance data: {e}")

    async def load_performance_data(self) -> None:
        """Load performance data from storage."""
        try:
            if self.storage_path.exists():
                with open(self.storage_path) as f:
                    self.domain_performance = json.load(f)
                logger.debug(f"Loaded performance data from {self.storage_path}")
            else:
                logger.debug("No existing performance data found")
        except Exception as e:
            logger.error(f"Failed to load performance data: {e}")
            self.domain_performance = {}

    async def cleanup_old_data(self, current_time: Optional[float] = None) -> None:
        """Remove performance data older than max_history_days."""
        if current_time is None:
            current_time = time.time()
        cutoff_time = current_time - (self.max_history_days * 24 * 60 * 60)

        for domain in self.domain_performance:
            for backend_name in self.domain_performance[domain]:
                backend_data = self.domain_performance[domain][backend_name]

                # Filter out old entries
                old_history = backend_data["history"]
                new_history = [
                    entry for entry in old_history if entry["timestamp"] > cutoff_time
                ]

                if len(new_history) != len(old_history):
                    backend_data["history"] = new_history

                    # Recalculate averages if we have data
                    if new_history:
                        backend_data["average_response_time"] = mean(
                            [m["response_time"] for m in new_history]
                        )
                        backend_data["average_memory_usage"] = mean(
                            [m["memory_usage"] for m in new_history]
                        )
                        backend_data["average_cpu_usage"] = mean(
                            [m["cpu_usage"] for m in new_history]
                        )
                        backend_data["success_rate"] = mean(
                            [1.0 if m["success"] else 0.0 for m in new_history]
                        )
                        backend_data["total_requests"] = len(new_history)
                    else:
                        # No data left, reset
                        backend_data.update(
                            {
                                "average_response_time": 0.0,
                                "average_memory_usage": 0.0,
                                "average_cpu_usage": 0.0,
                                "success_rate": 0.0,
                                "total_requests": 0,
                            }
                        )

        logger.debug(
            f"Cleaned up performance data older than {self.max_history_days} days"
        )

    async def start_monitoring(
        self, backend_name: str, domain: str
    ) -> MonitoringContext:
        """
        Start monitoring a backend operation.

        Args:
            backend_name: Name of the backend
            domain: Domain being crawled

        Returns:
            Monitoring context
        """
        start_time = time.time()
        start_memory = 0.0
        start_cpu = 0.0
        process = None

        if PSUTIL_AVAILABLE:
            try:
                process = psutil.Process()
                start_memory = process.memory_info().rss / 1024 / 1024  # MB
                start_cpu = process.cpu_percent()
            except Exception as e:
                logger.warning(f"Failed to get initial system metrics: {e}")

        return MonitoringContext(
            backend_name=backend_name,
            domain=domain,
            start_time=start_time,
            start_memory=start_memory,
            start_cpu=start_cpu,
            process=process,
        )

    async def stop_monitoring(self, context: MonitoringContext) -> dict[str, Any]:
        """
        Stop monitoring and return performance metrics.

        Args:
            context: Monitoring context from start_monitoring

        Returns:
            Performance metrics dictionary
        """
        end_time = time.time()
        response_time = end_time - context.start_time

        memory_usage = 0.0
        cpu_usage = 0.0

        if PSUTIL_AVAILABLE and context.process:
            try:
                end_memory = context.process.memory_info().rss / 1024 / 1024  # MB
                memory_usage = max(0, end_memory - context.start_memory)
                cpu_usage = context.process.cpu_percent()
            except Exception as e:
                logger.warning(f"Failed to get final system metrics: {e}")

        metrics = {
            "response_time": response_time,
            "memory_usage": memory_usage,
            "cpu_usage": cpu_usage,
            "success": True,  # Will be updated by caller if needed
            "content_size": 0,  # Will be updated by caller
            "timestamp": end_time,
        }

        return metrics
