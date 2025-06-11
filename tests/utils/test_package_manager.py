"""
Tests for the package manager.
"""

from unittest.mock import AsyncMock, patch

import pytest

from src.utils.package_manager import PackageManager, PackageManagerConfig


@pytest.fixture
def package_manager():
    """Create a package manager for testing."""
    config = PackageManagerConfig(
        use_uv=True, uv_path="/usr/bin/uv", pip_path="/usr/bin/pip"
    )
    return PackageManager(config=config)


@pytest.mark.asyncio
async def test_install_package_with_uv(package_manager):
    """Test installing a package with uv."""
    # Mock the subprocess
    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        # Set up the mock process
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(
            return_value=(b"Successfully installed", b"")
        )
        mock_process.returncode = 0
        mock_exec.return_value = mock_process

        # Call the method
        success, output = await package_manager.install_package("hypothesis")

        # Check the result
        assert success is True
        assert "Successfully installed" in output

        # Check that the correct command was called
        mock_exec.assert_called_once()
        args, kwargs = mock_exec.call_args
        assert args[0] == "/usr/bin/uv"
        assert args[1] == "pip"
        assert args[2] == "install"
        assert args[3] == "hypothesis"


@pytest.mark.asyncio
async def test_install_package_with_version(package_manager):
    """Test installing a package with a specific version."""
    # Mock the subprocess
    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        # Set up the mock process
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(
            return_value=(b"Successfully installed", b"")
        )
        mock_process.returncode = 0
        mock_exec.return_value = mock_process

        # Call the method
        success, output = await package_manager.install_package(
            "hypothesis", version="6.92.1"
        )

        # Check the result
        assert success is True
        assert "Successfully installed" in output

        # Check that the correct command was called
        mock_exec.assert_called_once()
        args, kwargs = mock_exec.call_args
        assert args[0] == "/usr/bin/uv"
        assert args[1] == "pip"
        assert args[2] == "install"
        assert args[3] == "hypothesis==6.92.1"


@pytest.mark.asyncio
async def test_install_package_with_pip_fallback():
    """Test installing a package with pip when uv is not available."""
    # Create a package manager with uv disabled
    config = PackageManagerConfig(use_uv=False, pip_path="/usr/bin/pip")
    package_manager = PackageManager(config=config)

    # Mock the subprocess
    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        # Set up the mock process
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(
            return_value=(b"Successfully installed", b"")
        )
        mock_process.returncode = 0
        mock_exec.return_value = mock_process

        # Call the method
        success, output = await package_manager.install_package("hypothesis")

        # Check the result
        assert success is True
        assert "Successfully installed" in output

        # Check that the correct command was called
        mock_exec.assert_called_once()
        args, kwargs = mock_exec.call_args
        assert args[0] == "/usr/bin/pip"
        assert args[1] == "install"
        assert args[2] == "hypothesis"


@pytest.mark.asyncio
async def test_uninstall_package(package_manager):
    """Test uninstalling a package."""
    # Mock the subprocess
    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        # Set up the mock process
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(
            return_value=(b"Successfully uninstalled", b"")
        )
        mock_process.returncode = 0
        mock_exec.return_value = mock_process

        # Call the method
        success, output = await package_manager.uninstall_package("hypothesis")

        # Check the result
        assert success is True
        assert "Successfully uninstalled" in output

        # Check that the correct command was called
        mock_exec.assert_called_once()
        args, kwargs = mock_exec.call_args
        assert args[0] == "/usr/bin/uv"
        assert args[1] == "pip"
        assert args[2] == "uninstall"
        assert args[3] == "-y"
        assert args[4] == "hypothesis"


@pytest.mark.asyncio
async def test_install_package_error(package_manager):
    """Test handling errors when installing a package."""
    # Mock the subprocess
    with patch("asyncio.create_subprocess_exec", new_callable=AsyncMock) as mock_exec:
        # Set up the mock process
        mock_process = AsyncMock()
        mock_process.communicate = AsyncMock(
            return_value=(b"", b"Error: Package not found")
        )
        mock_process.returncode = 1
        mock_exec.return_value = mock_process

        # Call the method
        success, output = await package_manager.install_package("nonexistent-package")

        # Check the result
        assert success is False
        assert "Error: Package not found" in output
