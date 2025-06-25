"""
Visualization tools for lib2docScrape.
"""

# Import only what's available to avoid import errors during testing
try:
    from .version_history import (
        VersionEdge,
        VersionGraph,
        VersionHistoryVisualizer,
        VersionNode,
    )

    __all__ = ["VersionHistoryVisualizer", "VersionGraph", "VersionNode", "VersionEdge"]
except ImportError:
    # During testing, some modules may not be available
    __all__ = []
