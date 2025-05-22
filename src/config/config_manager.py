"""
Configuration management for the lib2docScrape system.
"""
import json
import logging
import os
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Type, TypeVar, Union, cast

import yaml
from pydantic import BaseModel, ValidationError, create_model

from ..utils.error_handler import ErrorCategory, ErrorLevel, handle_error

logger = logging.getLogger(__name__)

T = TypeVar('T', bound=BaseModel)

class ConfigFormat(Enum):
    """Supported configuration file formats."""
    JSON = "json"
    YAML = "yaml"
    TOML = "toml"

class ConfigPreset(Enum):
    """Predefined configuration presets."""
    DEFAULT = "default"
    MINIMAL = "minimal"
    PERFORMANCE = "performance"
    QUALITY = "quality"
    JAVASCRIPT = "javascript"

class ConfigManager:
    """
    Configuration manager for the lib2docScrape system.

    This class provides methods for loading, validating, and managing
    configuration settings for all components of the system.
    """

    def __init__(self, config_dir: Optional[str] = None):
        """
        Initialize the configuration manager.

        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = config_dir or os.path.join(os.path.dirname(__file__), "presets")
        self.configs: Dict[str, Dict[str, Any]] = {}
        self.model_registry: Dict[str, Type[BaseModel]] = {}

    def register_model(self, name: str, model: Type[BaseModel]) -> None:
        """
        Register a configuration model.

        Args:
            name: Name of the configuration section
            model: Pydantic model class for validation
        """
        self.model_registry[name] = model

    def load_config(
        self,
        config_path: Optional[str] = None,
        format: ConfigFormat = ConfigFormat.YAML
    ) -> Dict[str, Any]:
        """
        Load configuration from a file.

        Args:
            config_path: Path to the configuration file
            format: Format of the configuration file

        Returns:
            Dictionary containing the configuration

        Raises:
            FileNotFoundError: If the configuration file does not exist
            ValueError: If the configuration file is invalid
        """
        if not config_path:
            config_path = os.path.join(self.config_dir, f"default.{format.value}")

        try:
            with open(config_path, "r") as f:
                if format == ConfigFormat.JSON:
                    config = json.load(f)
                elif format == ConfigFormat.YAML:
                    config = yaml.safe_load(f)
                elif format == ConfigFormat.TOML:
                    import toml
                    config = toml.load(f)
                else:
                    raise ValueError(f"Unsupported configuration format: {format}")

            # Store the loaded configuration
            self.configs["main"] = config
            return config

        except FileNotFoundError:
            error = FileNotFoundError(f"Configuration file not found: {config_path}")
            handle_error(
                error,
                "ConfigManager",
                "load_config",
                details={"config_path": config_path},
                level=ErrorLevel.ERROR,
                category=ErrorCategory.CONFIGURATION
            )
            raise error
        except Exception as e:
            error_details = {
                "config_path": config_path,
                "format": format.value
            }
            handle_error(
                e,
                "ConfigManager",
                "load_config",
                details=error_details,
                level=ErrorLevel.ERROR,
                category=ErrorCategory.CONFIGURATION
            )
            raise ValueError(f"Failed to load configuration: {str(e)}") from e

    def validate_config(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate configuration against registered models.

        Args:
            config: Configuration dictionary to validate

        Returns:
            Validated configuration dictionary

        Raises:
            ValidationError: If the configuration is invalid
        """
        validated_config = {}
        errors = []

        for section, model in self.model_registry.items():
            if section in config:
                try:
                    # Validate the section using the registered model
                    validated_section = model(**config[section])
                    validated_config[section] = validated_section.model_dump()
                except ValidationError as e:
                    errors.append(f"Validation error in section '{section}': {str(e)}")
            else:
                # If section is missing, create it with default values
                validated_config[section] = model().model_dump()

        if errors:
            error_message = "\n".join(errors)
            # Create a custom exception instead of ValidationError
            error = ValueError(f"Configuration validation failed: {error_message}")
            handle_error(
                error,
                "ConfigManager",
                "validate_config",
                details={"errors": errors},
                level=ErrorLevel.ERROR,
                category=ErrorCategory.VALIDATION
            )
            raise error

        return validated_config

    def get_config(self, section: Optional[str] = None, model_type: Optional[Type[T]] = None) -> Union[Dict[str, Any], T]:
        """
        Get configuration for a specific section.

        Args:
            section: Name of the configuration section
            model_type: Optional model type to cast the result to

        Returns:
            Configuration dictionary or model instance
        """
        if not self.configs:
            self.load_config()

        config = self.configs.get("main", {})

        if section:
            if section not in config:
                # If section is missing but we have a registered model, create default
                if section in self.model_registry:
                    config[section] = self.model_registry[section]().model_dump()
                else:
                    return {} if model_type is None else model_type()

            section_config = config[section]

            if model_type:
                try:
                    return model_type(**section_config)
                except ValidationError as e:
                    handle_error(
                        e,
                        "ConfigManager",
                        "get_config",
                        details={"section": section},
                        level=ErrorLevel.WARNING,
                        category=ErrorCategory.VALIDATION
                    )
                    return model_type()
            return section_config
        else:
            return config

    def save_config(
        self,
        config: Dict[str, Any],
        config_path: str,
        format: ConfigFormat = ConfigFormat.YAML
    ) -> None:
        """
        Save configuration to a file.

        Args:
            config: Configuration dictionary to save
            config_path: Path to save the configuration to
            format: Format to save the configuration in
        """
        try:
            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(config_path), exist_ok=True)

            with open(config_path, "w") as f:
                if format == ConfigFormat.JSON:
                    json.dump(config, f, indent=2)
                elif format == ConfigFormat.YAML:
                    yaml.dump(config, f, default_flow_style=False)
                elif format == ConfigFormat.TOML:
                    import toml
                    toml.dump(config, f)
                else:
                    raise ValueError(f"Unsupported configuration format: {format}")

        except Exception as e:
            error_details = {
                "config_path": config_path,
                "format": format.value
            }
            handle_error(
                e,
                "ConfigManager",
                "save_config",
                details=error_details,
                level=ErrorLevel.ERROR,
                category=ErrorCategory.CONFIGURATION
            )
            raise ValueError(f"Failed to save configuration: {str(e)}") from e

    def load_preset(self, preset: ConfigPreset) -> Dict[str, Any]:
        """
        Load a predefined configuration preset.

        Args:
            preset: Preset to load

        Returns:
            Configuration dictionary for the preset
        """
        preset_path = os.path.join(self.config_dir, f"{preset.value}.yaml")
        return self.load_config(preset_path)

    def merge_configs(self, base_config: Dict[str, Any], override_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge two configuration dictionaries.

        Args:
            base_config: Base configuration
            override_config: Configuration to override base with

        Returns:
            Merged configuration dictionary
        """
        result = base_config.copy()

        for key, value in override_config.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                result[key] = self.merge_configs(result[key], value)
            else:
                # Override or add the value
                result[key] = value

        return result

# Global configuration manager instance
config_manager = ConfigManager()

def register_config_model(name: str, model: Type[BaseModel]) -> None:
    """
    Register a configuration model with the global config manager.

    Args:
        name: Name of the configuration section
        model: Pydantic model class for validation
    """
    config_manager.register_model(name, model)

def get_config(section: Optional[str] = None, model_type: Optional[Type[T]] = None) -> Union[Dict[str, Any], T]:
    """
    Get configuration from the global config manager.

    Args:
        section: Name of the configuration section
        model_type: Optional model type to cast the result to

    Returns:
        Configuration dictionary or model instance
    """
    return config_manager.get_config(section, model_type)

def load_config(config_path: Optional[str] = None, format: ConfigFormat = ConfigFormat.YAML) -> Dict[str, Any]:
    """
    Load configuration using the global config manager.

    Args:
        config_path: Path to the configuration file
        format: Format of the configuration file

    Returns:
        Dictionary containing the configuration
    """
    return config_manager.load_config(config_path, format)

def load_preset(preset: ConfigPreset) -> Dict[str, Any]:
    """
    Load a predefined configuration preset using the global config manager.

    Args:
        preset: Preset to load

    Returns:
        Configuration dictionary for the preset
    """
    return config_manager.load_preset(preset)
