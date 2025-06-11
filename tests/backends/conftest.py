from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def mock_aiohttp_session():
    """
    Fixture to create a mock aiohttp session and response.

    Returns:
        Tuple[MagicMock, AsyncMock]: A mock session and a mock response
    """

    def _create_mock_session(response_body="", status=200, content_type="text/html"):
        # Create mock response
        mock_response = AsyncMock()
        mock_response.status = status
        mock_response.headers = {"Content-Type": content_type}
        mock_response.text = AsyncMock(return_value=response_body)

        # Create mock context manager for session.get()
        mock_cm = AsyncMock()
        mock_cm.__aenter__.return_value = mock_response
        mock_cm.__aexit__.return_value = None

        # Create mock session
        mock_session = AsyncMock()
        mock_session.get = MagicMock(return_value=mock_cm)

        return mock_session, mock_response

    return _create_mock_session
