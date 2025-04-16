"""
Type definitions and enumerations for URL handling.
"""

from enum import Enum, auto

class URLType(Enum):
    """URL classification type based on the relationship to a base URL."""
    INTERNAL = auto()
    EXTERNAL = auto()
    UNKNOWN = auto()