"""
Error handling utilities for the lib2docScrape system.
"""

import logging
import traceback
from enum import Enum
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class ErrorLevel(Enum):
    """Error severity levels."""

    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Categories of errors."""

    NETWORK = "network"
    PARSING = "parsing"
    VALIDATION = "validation"
    CONFIGURATION = "configuration"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    RESOURCE = "resource"
    TIMEOUT = "timeout"
    INTERNAL = "internal"
    EXTERNAL = "external"
    UNKNOWN = "unknown"


class ErrorContext:
    """Context information for an error."""

    def __init__(
        self,
        component: str,
        operation: str,
        url: Optional[str] = None,
        details: Optional[dict[str, Any]] = None,
    ):
        """
        Initialize error context.

        Args:
            component: Component where the error occurred
            operation: Operation being performed
            url: Optional URL being processed
            details: Optional additional details
        """
        self.component = component
        self.operation = operation
        self.url = url
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "component": self.component,
            "operation": self.operation,
            "url": self.url,
            **self.details,
        }


class ErrorHandler:
    """
    Centralized error handling for the lib2docScrape system.

    This class provides methods for handling errors consistently across
    the system, including logging, categorization, and recovery strategies.
    """

    def __init__(self):
        """Initialize the error handler."""
        self.error_callbacks: dict[ErrorCategory, list[Callable]] = {}
        self.error_counts: dict[ErrorCategory, int] = dict.fromkeys(ErrorCategory, 0)

    def register_callback(self, category: ErrorCategory, callback: Callable) -> None:
        """
        Register a callback for a specific error category.

        Args:
            category: Error category to register for
            callback: Function to call when an error of this category occurs
        """
        if category not in self.error_callbacks:
            self.error_callbacks[category] = []
        self.error_callbacks[category].append(callback)

    def handle_error(
        self,
        error: Exception,
        context: ErrorContext,
        level: ErrorLevel = ErrorLevel.ERROR,
        category: Optional[ErrorCategory] = None,
    ) -> dict[str, Any]:
        """
        Handle an error.

        Args:
            error: The exception that occurred
            context: Context information for the error
            level: Severity level of the error
            category: Category of the error (auto-detected if None)

        Returns:
            Dictionary with error details
        """
        # Auto-detect category if not provided
        if category is None:
            category = self._categorize_error(error)

        # Update error count
        self.error_counts[category] += 1

        # Create error details
        error_details = {
            "error_message": str(
                error
            ),  # Changed from "message" to avoid conflict with LogRecord
            "type": type(error).__name__,
            "category": category.value,
            "level": level.value,
            "context": context.to_dict(),
            "traceback": traceback.format_exc(),
        }

        # Log the error
        self._log_error(error_details, level)

        # Call registered callbacks
        self._call_callbacks(category, error, error_details)

        return error_details

    def _categorize_error(self, error: Exception) -> ErrorCategory:
        """
        Categorize an error based on its type.

        Args:
            error: The exception to categorize

        Returns:
            ErrorCategory for the error
        """
        error_type = type(error).__name__.lower()
        error_msg = str(error).lower()

        # Check both error type and message content
        if any(
            net_err in error_type
            for net_err in ["connection", "network", "http", "socket", "dns"]
        ) or any(
            net_err in error_msg
            for net_err in ["network", "connection", "http", "socket", "dns"]
        ):
            return ErrorCategory.NETWORK
        elif any(
            parse_err in error_type
            for parse_err in ["parse", "syntax", "value", "type", "attribute"]
        ):
            return ErrorCategory.PARSING
        elif any(
            valid_err in error_type for valid_err in ["validation", "valid", "schema"]
        ) or any(
            valid_err in error_msg for valid_err in ["validation", "valid", "schema"]
        ):
            return ErrorCategory.VALIDATION
        elif any(
            config_err in error_type for config_err in ["config", "setting", "option"]
        ) or any(
            config_err in error_msg for config_err in ["config", "setting", "option"]
        ):
            return ErrorCategory.CONFIGURATION
        elif any(
            auth_err in error_type for auth_err in ["auth", "login", "credential"]
        ):
            return ErrorCategory.AUTHENTICATION
        elif any(
            perm_err in error_type for perm_err in ["permission", "access", "forbidden"]
        ):
            return ErrorCategory.AUTHORIZATION
        elif any(
            res_err in error_type for res_err in ["resource", "memory", "disk", "file"]
        ):
            return ErrorCategory.RESOURCE
        elif any(time_err in error_type for time_err in ["timeout", "deadline"]):
            return ErrorCategory.TIMEOUT
        elif "internal" in error_type:
            return ErrorCategory.INTERNAL
        elif "external" in error_type:
            return ErrorCategory.EXTERNAL
        else:
            return ErrorCategory.UNKNOWN

    def _log_error(self, error_details: dict[str, Any], level: ErrorLevel) -> None:
        """
        Log an error with the appropriate severity level.

        Args:
            error_details: Details of the error
            level: Severity level of the error
        """
        message = f"{error_details['type']}: {error_details['error_message']} in {error_details['context']['component']}.{error_details['context']['operation']}"

        if level == ErrorLevel.DEBUG:
            logger.debug(message, extra=error_details)
        elif level == ErrorLevel.INFO:
            logger.info(message, extra=error_details)
        elif level == ErrorLevel.WARNING:
            logger.warning(message, extra=error_details)
        elif level == ErrorLevel.ERROR:
            logger.error(message, extra=error_details)
        elif level == ErrorLevel.CRITICAL:
            logger.critical(message, extra=error_details)

    def _call_callbacks(
        self, category: ErrorCategory, error: Exception, error_details: dict[str, Any]
    ) -> None:
        """
        Call registered callbacks for an error category.

        Args:
            category: Category of the error
            error: The exception that occurred
            error_details: Details of the error
        """
        if category in self.error_callbacks:
            for callback in self.error_callbacks[category]:
                try:
                    # Create a copy of error_details with message for backward compatibility
                    callback_details = error_details.copy()
                    if (
                        "error_message" in callback_details
                        and "message" not in callback_details
                    ):
                        callback_details["message"] = callback_details["error_message"]

                    callback(error, callback_details)
                except Exception as e:
                    logger.error(f"Error in error callback: {str(e)}")

    def get_error_counts(self) -> dict[str, int]:
        """
        Get the count of errors by category.

        Returns:
            Dictionary mapping error category names to counts
        """
        return {category.value: count for category, count in self.error_counts.items()}

    def reset_error_counts(self) -> None:
        """Reset all error counts to zero."""
        self.error_counts = dict.fromkeys(ErrorCategory, 0)


# Global error handler instance
error_handler = ErrorHandler()


def handle_error(
    error: Exception,
    component: str,
    operation: str,
    url: Optional[str] = None,
    details: Optional[dict[str, Any]] = None,
    level: ErrorLevel = ErrorLevel.ERROR,
    category: Optional[ErrorCategory] = None,
) -> dict[str, Any]:
    """
    Handle an error using the global error handler.

    Args:
        error: The exception that occurred
        component: Component where the error occurred
        operation: Operation being performed
        url: Optional URL being processed
        details: Optional additional details
        level: Severity level of the error
        category: Category of the error (auto-detected if None)

    Returns:
        Dictionary with error details
    """
    context = ErrorContext(component, operation, url, details)
    return error_handler.handle_error(error, context, level, category)


def register_error_callback(category: ErrorCategory, callback: Callable) -> None:
    """
    Register a callback for a specific error category.

    Args:
        category: Error category to register for
        callback: Function to call when an error of this category occurs
    """
    error_handler.register_callback(category, callback)


def get_error_counts() -> dict[str, int]:
    """
    Get the count of errors by category.

    Returns:
        Dictionary mapping error category names to counts
    """
    return error_handler.get_error_counts()


def reset_error_counts() -> None:
    """Reset all error counts to zero."""
    error_handler.reset_error_counts()
