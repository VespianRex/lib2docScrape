"""
Tests for the dashboard UI module.
"""

from unittest.mock import MagicMock, patch

from fastapi.responses import HTMLResponse
from fastapi.testclient import TestClient

from src.main import app
from src.ui.dashboard import Dashboard, DashboardConfig

client = TestClient(app)


def test_dashboard_config_defaults():
    """Test DashboardConfig default values."""
    config = DashboardConfig()
    assert config.title == "lib2docScrape Dashboard"
    assert config.theme == "light"
    assert config.refresh_interval == 5
    assert config.max_items_per_page == 20
    assert config.enable_charts is True
    assert config.enable_search is True
    assert config.enable_filters is True
    assert config.enable_export is True


def test_dashboard_config_custom():
    """Test DashboardConfig with custom values."""
    config = DashboardConfig(
        title="Custom Dashboard",
        theme="dark",
        refresh_interval=60,
        max_items_per_page=50,
        enable_charts=False,
        enable_search=False,
        enable_filters=False,
        enable_export=False,
    )
    assert config.title == "Custom Dashboard"
    assert config.theme == "dark"
    assert config.refresh_interval == 60
    assert config.max_items_per_page == 50
    assert config.enable_charts is False
    assert config.enable_search is False
    assert config.enable_filters is False
    assert config.enable_export is False


@patch("src.ui.dashboard.Jinja2Templates")
def test_dashboard_ui_initialization(mock_templates):
    """Test Dashboard initialization."""
    mock_template_instance = MagicMock()
    mock_templates.return_value = mock_template_instance

    # Create a mock FastAPI app
    mock_app = MagicMock()

    dashboard = Dashboard(app=mock_app)

    assert dashboard.config.title == "lib2docScrape Dashboard"
    assert dashboard.templates is mock_template_instance
    mock_templates.assert_called_once()


@patch("src.ui.dashboard.Jinja2Templates")
def test_dashboard_ui_with_custom_config(mock_templates):
    """Test Dashboard with custom config."""
    mock_template_instance = MagicMock()
    mock_templates.return_value = mock_template_instance

    # Create a mock FastAPI app
    mock_app = MagicMock()

    config = DashboardConfig(title="Custom Dashboard", theme="dark")
    dashboard = Dashboard(app=mock_app, config=config)

    assert dashboard.config.title == "Custom Dashboard"
    assert dashboard.config.theme == "dark"
    assert dashboard.templates is mock_template_instance


@patch("fastapi.templating.Jinja2Templates.TemplateResponse")
def test_dashboard_render_dashboard(mock_template_response):
    """Test rendering the dashboard."""
    mock_template_response.return_value = {"status": "success"}

    # Create a mock FastAPI app
    mock_app = MagicMock()
    Dashboard(app=mock_app)

    # Test the home route handler
    MagicMock()

    # Get the home route handler
    home_route = None
    for route in mock_app.get.call_args_list:
        if route[0][0] == "/":
            home_route = route[1]["response_class"]
            break

    assert home_route is not None
    assert home_route == HTMLResponse


def test_dashboard_api_status():
    """Test the API status endpoint."""
    # Create a mock FastAPI app
    mock_app = MagicMock()
    Dashboard(app=mock_app)

    # Find the API status route handler
    status_handler = None
    for route in mock_app.get.call_args_list:
        if route[0][0] == "/api/status":
            # The route handler is registered
            status_handler = True
            break

    # The API status route should be registered
    assert status_handler is not None


def test_dashboard_api_config():
    """Test the API config endpoint."""
    # Create a mock FastAPI app
    mock_app = MagicMock()
    config = DashboardConfig(title="Test Dashboard", theme="dark")
    Dashboard(app=mock_app, config=config)

    # Find the API config route handler
    config_handler = None
    for route in mock_app.get.call_args_list:
        if route[0][0] == "/api/config":
            # The route handler is registered
            config_handler = True
            break

    # The API config route should be registered
    assert config_handler is not None


def test_dashboard_websocket_setup():
    """Test WebSocket setup."""
    # Create a mock FastAPI app with enable_websockets=True
    mock_app = MagicMock()
    config = DashboardConfig(enable_websockets=True)
    Dashboard(app=mock_app, config=config)

    # Find the WebSocket route handler
    ws_handler = None
    for route in mock_app.websocket.call_args_list:
        if route[0][0] == "/ws":
            ws_handler = route[1]
            break

    # The WebSocket route should be registered
    assert ws_handler is not None

    # Test with WebSockets disabled
    mock_app = MagicMock()
    config = DashboardConfig(enable_websockets=False)
    Dashboard(app=mock_app, config=config)

    # The app.websocket method should not be called
    mock_app.websocket.assert_not_called()
