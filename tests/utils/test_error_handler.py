"""
Tests for the error handling utilities.
"""
import pytest
from unittest.mock import MagicMock, patch

from src.utils.error_handler import (
    ErrorHandler,
    ErrorContext,
    ErrorLevel,
    ErrorCategory,
    handle_error,
    register_error_callback,
    get_error_counts,
    reset_error_counts
)

def test_error_context():
    """Test ErrorContext initialization and to_dict method."""
    context = ErrorContext(
        component="test_component",
        operation="test_operation",
        url="https://example.com",
        details={"param1": "value1", "param2": 123}
    )

    assert context.component == "test_component"
    assert context.operation == "test_operation"
    assert context.url == "https://example.com"
    assert context.details == {"param1": "value1", "param2": 123}

    context_dict = context.to_dict()
    assert context_dict["component"] == "test_component"
    assert context_dict["operation"] == "test_operation"
    assert context_dict["url"] == "https://example.com"
    assert context_dict["param1"] == "value1"
    assert context_dict["param2"] == 123

def test_error_handler_categorize():
    """Test error categorization."""
    handler = ErrorHandler()

    # Test network errors
    assert handler._categorize_error(ConnectionError()) == ErrorCategory.NETWORK
    assert handler._categorize_error(Exception("network error")) == ErrorCategory.NETWORK

    # Test parsing errors
    assert handler._categorize_error(ValueError()) == ErrorCategory.PARSING
    assert handler._categorize_error(TypeError()) == ErrorCategory.PARSING
    assert handler._categorize_error(AttributeError()) == ErrorCategory.PARSING

    # Test validation errors
    assert handler._categorize_error(Exception("validation error")) == ErrorCategory.VALIDATION

    # Test configuration errors
    assert handler._categorize_error(Exception("config error")) == ErrorCategory.CONFIGURATION

    # Test timeout errors
    assert handler._categorize_error(TimeoutError()) == ErrorCategory.TIMEOUT

    # Test unknown errors
    assert handler._categorize_error(Exception("some random error")) == ErrorCategory.UNKNOWN

def test_error_handler_callbacks():
    """Test error callback registration and execution."""
    handler = ErrorHandler()

    # Create mock callbacks
    network_callback = MagicMock()
    parsing_callback = MagicMock()

    # Register callbacks
    handler.register_callback(ErrorCategory.NETWORK, network_callback)
    handler.register_callback(ErrorCategory.PARSING, parsing_callback)

    # Handle a network error
    error = ConnectionError("Failed to connect")
    context = ErrorContext("test", "connect", "https://example.com")

    # Patch the _log_error method to avoid logging issues
    with patch.object(handler, '_log_error'):
        handler.handle_error(error, context, category=ErrorCategory.NETWORK)

        # Check that the network callback was called
        network_callback.assert_called_once()
        parsing_callback.assert_not_called()

        # Reset mocks
        network_callback.reset_mock()
        parsing_callback.reset_mock()

        # Handle a parsing error
        error = ValueError("Invalid value")
        context = ErrorContext("test", "parse", "https://example.com")
        handler.handle_error(error, context, category=ErrorCategory.PARSING)

        # Check that the parsing callback was called
        parsing_callback.assert_called_once()
        network_callback.assert_not_called()

def test_error_handler_logging():
    """Test error logging."""
    handler = ErrorHandler()

    # Mock the logger
    with patch("src.utils.error_handler.logger") as mock_logger:
        # Handle errors at different levels
        error = ValueError("Test error")
        context = ErrorContext("test", "operation")

        # Debug level
        handler.handle_error(error, context, level=ErrorLevel.DEBUG)
        mock_logger.debug.assert_called_once()
        mock_logger.info.assert_not_called()
        mock_logger.warning.assert_not_called()
        mock_logger.error.assert_not_called()
        mock_logger.critical.assert_not_called()
        mock_logger.reset_mock()

        # Info level
        handler.handle_error(error, context, level=ErrorLevel.INFO)
        mock_logger.debug.assert_not_called()
        mock_logger.info.assert_called_once()
        mock_logger.warning.assert_not_called()
        mock_logger.error.assert_not_called()
        mock_logger.critical.assert_not_called()
        mock_logger.reset_mock()

        # Warning level
        handler.handle_error(error, context, level=ErrorLevel.WARNING)
        mock_logger.debug.assert_not_called()
        mock_logger.info.assert_not_called()
        mock_logger.warning.assert_called_once()
        mock_logger.error.assert_not_called()
        mock_logger.critical.assert_not_called()
        mock_logger.reset_mock()

        # Error level
        handler.handle_error(error, context, level=ErrorLevel.ERROR)
        mock_logger.debug.assert_not_called()
        mock_logger.info.assert_not_called()
        mock_logger.warning.assert_not_called()
        mock_logger.error.assert_called_once()
        mock_logger.critical.assert_not_called()
        mock_logger.reset_mock()

        # Critical level
        handler.handle_error(error, context, level=ErrorLevel.CRITICAL)
        mock_logger.debug.assert_not_called()
        mock_logger.info.assert_not_called()
        mock_logger.warning.assert_not_called()
        mock_logger.error.assert_not_called()
        mock_logger.critical.assert_called_once()

def test_error_counts():
    """Test error counting and resetting."""
    handler = ErrorHandler()

    # Handle errors of different categories
    error = Exception("Test error")
    context = ErrorContext("test", "operation")

    # Patch the _log_error method to avoid logging issues
    with patch.object(handler, '_log_error'):
        handler.handle_error(error, context, category=ErrorCategory.NETWORK)
        handler.handle_error(error, context, category=ErrorCategory.NETWORK)
        handler.handle_error(error, context, category=ErrorCategory.PARSING)

        # Check error counts
        counts = handler.get_error_counts()
        assert counts[ErrorCategory.NETWORK.value] == 2
        assert counts[ErrorCategory.PARSING.value] == 1
        assert counts[ErrorCategory.VALIDATION.value] == 0

        # Reset counts
        handler.reset_error_counts()

        # Check that counts are reset
        counts = handler.get_error_counts()
        assert counts[ErrorCategory.NETWORK.value] == 0
        assert counts[ErrorCategory.PARSING.value] == 0

def test_global_functions():
    """Test the global error handling functions."""
    # Mock the global error handler
    with patch("src.utils.error_handler.error_handler") as mock_handler:
        # Test handle_error
        error = ValueError("Test error")
        handle_error(error, "test", "operation", "https://example.com")
        mock_handler.handle_error.assert_called_once()

        # Test register_error_callback
        callback = MagicMock()
        register_error_callback(ErrorCategory.NETWORK, callback)
        mock_handler.register_callback.assert_called_once_with(ErrorCategory.NETWORK, callback)

        # Test get_error_counts
        get_error_counts()
        mock_handler.get_error_counts.assert_called_once()

        # Test reset_error_counts
        reset_error_counts()
        mock_handler.reset_error_counts.assert_called_once()
