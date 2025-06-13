"""
Performance tracking and optimization module for lib2docScrape.

This module provides performance tracking capabilities for different backends,
allowing the system to automatically select the most efficient backend based
on historical performance data.
"""

from .backend_tracker import BackendPerformanceTracker, PerformanceMetrics, MonitoringContext

__all__ = [
    "BackendPerformanceTracker",
    "PerformanceMetrics", 
    "MonitoringContext"
]
