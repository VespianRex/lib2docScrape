"""
Package management utilities for lib2docScrape.
Provides integration with uv for Python package management.
"""
import asyncio
import logging
import os
import platform
import shutil
import subprocess
import sys
from typing import List, Optional, Tuple, Dict, Any, Union

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

class PackageManagerConfig(BaseModel):
    """Configuration for package management."""
    use_uv: bool = True
    uv_path: Optional[str] = None
    pip_path: Optional[str] = None
    venv_path: Optional[str] = None
    cache_dir: Optional[str] = None
    index_url: Optional[str] = None
    extra_index_urls: List[str] = Field(default_factory=list)
    trusted_hosts: List[str] = Field(default_factory=list)
    timeout: int = 60
    retries: int = 3
    verbose: bool = False

class PackageManager:
    """
    Package manager for Python packages.
    Provides integration with uv and fallback to pip.
    """
    
    def __init__(self, config: Optional[PackageManagerConfig] = None):
        """
        Initialize the package manager.
        
        Args:
            config: Optional configuration for the package manager
        """
        self.config = config or PackageManagerConfig()
        self._find_executables()
        
    def _find_executables(self) -> None:
        """Find package manager executables."""
        # Find uv
        if self.config.uv_path:
            self.uv_path = self.config.uv_path
        else:
            self.uv_path = shutil.which("uv")
            
        # Find pip
        if self.config.pip_path:
            self.pip_path = self.config.pip_path
        else:
            self.pip_path = shutil.which("pip") or shutil.which("pip3")
            
        # Log availability
        if self.uv_path:
            logger.info(f"Found uv at {self.uv_path}")
        else:
            logger.info("uv not found in PATH")
            
        if self.pip_path:
            logger.info(f"Found pip at {self.pip_path}")
        else:
            logger.warning("pip not found in PATH")
            
    async def install_package(self, package_name: str, version: Optional[str] = None) -> Tuple[bool, str]:
        """
        Install a Python package.
        
        Args:
            package_name: Name of the package to install
            version: Optional version specifier
            
        Returns:
            Tuple of (success, output)
        """
        package_spec = f"{package_name}{f'=={version}' if version else ''}"
        
        if self.config.use_uv and self.uv_path:
            return await self._install_with_uv(package_spec)
        elif self.pip_path:
            return await self._install_with_pip(package_spec)
        else:
            error_msg = "No package manager available. Install uv or pip."
            logger.error(error_msg)
            return False, error_msg
            
    async def _install_with_uv(self, package_spec: str) -> Tuple[bool, str]:
        """
        Install a package using uv.
        
        Args:
            package_spec: Package specification (name and optional version)
            
        Returns:
            Tuple of (success, output)
        """
        cmd = [self.uv_path, "pip", "install", package_spec]
        
        # Add options
        if self.config.index_url:
            cmd.extend(["--index-url", self.config.index_url])
            
        for url in self.config.extra_index_urls:
            cmd.extend(["--extra-index-url", url])
            
        for host in self.config.trusted_hosts:
            cmd.extend(["--trusted-host", host])
            
        if self.config.cache_dir:
            cmd.extend(["--cache-dir", self.config.cache_dir])
            
        if self.config.verbose:
            cmd.append("--verbose")
            
        # Run the command
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            output = stdout.decode() + stderr.decode()
            success = process.returncode == 0
            
            if success:
                logger.info(f"Successfully installed {package_spec} with uv")
            else:
                logger.error(f"Failed to install {package_spec} with uv: {output}")
                
            return success, output
        except Exception as e:
            error_msg = f"Error installing {package_spec} with uv: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
            
    async def _install_with_pip(self, package_spec: str) -> Tuple[bool, str]:
        """
        Install a package using pip.
        
        Args:
            package_spec: Package specification (name and optional version)
            
        Returns:
            Tuple of (success, output)
        """
        cmd = [self.pip_path, "install", package_spec]
        
        # Add options
        if self.config.index_url:
            cmd.extend(["--index-url", self.config.index_url])
            
        for url in self.config.extra_index_urls:
            cmd.extend(["--extra-index-url", url])
            
        for host in self.config.trusted_hosts:
            cmd.extend(["--trusted-host", host])
            
        if self.config.cache_dir:
            cmd.extend(["--cache-dir", self.config.cache_dir])
            
        if self.config.verbose:
            cmd.append("--verbose")
            
        # Run the command
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            output = stdout.decode() + stderr.decode()
            success = process.returncode == 0
            
            if success:
                logger.info(f"Successfully installed {package_spec} with pip")
            else:
                logger.error(f"Failed to install {package_spec} with pip: {output}")
                
            return success, output
        except Exception as e:
            error_msg = f"Error installing {package_spec} with pip: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
            
    async def uninstall_package(self, package_name: str) -> Tuple[bool, str]:
        """
        Uninstall a Python package.
        
        Args:
            package_name: Name of the package to uninstall
            
        Returns:
            Tuple of (success, output)
        """
        if self.config.use_uv and self.uv_path:
            return await self._uninstall_with_uv(package_name)
        elif self.pip_path:
            return await self._uninstall_with_pip(package_name)
        else:
            error_msg = "No package manager available. Install uv or pip."
            logger.error(error_msg)
            return False, error_msg
            
    async def _uninstall_with_uv(self, package_name: str) -> Tuple[bool, str]:
        """
        Uninstall a package using uv.
        
        Args:
            package_name: Name of the package to uninstall
            
        Returns:
            Tuple of (success, output)
        """
        cmd = [self.uv_path, "pip", "uninstall", "-y", package_name]
        
        if self.config.verbose:
            cmd.append("--verbose")
            
        # Run the command
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            output = stdout.decode() + stderr.decode()
            success = process.returncode == 0
            
            if success:
                logger.info(f"Successfully uninstalled {package_name} with uv")
            else:
                logger.error(f"Failed to uninstall {package_name} with uv: {output}")
                
            return success, output
        except Exception as e:
            error_msg = f"Error uninstalling {package_name} with uv: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
            
    async def _uninstall_with_pip(self, package_name: str) -> Tuple[bool, str]:
        """
        Uninstall a package using pip.
        
        Args:
            package_name: Name of the package to uninstall
            
        Returns:
            Tuple of (success, output)
        """
        cmd = [self.pip_path, "uninstall", "-y", package_name]
        
        if self.config.verbose:
            cmd.append("--verbose")
            
        # Run the command
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await process.communicate()
            
            output = stdout.decode() + stderr.decode()
            success = process.returncode == 0
            
            if success:
                logger.info(f"Successfully uninstalled {package_name} with pip")
            else:
                logger.error(f"Failed to uninstall {package_name} with pip: {output}")
                
            return success, output
        except Exception as e:
            error_msg = f"Error uninstalling {package_name} with pip: {str(e)}"
            logger.error(error_msg)
            return False, error_msg
