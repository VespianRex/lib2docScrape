"""
Tests for the configuration management system.
"""

import os
import tempfile

import pytest
from pydantic import BaseModel

from src.config.config_manager import (
    ConfigFormat,
    ConfigManager,
    get_config,
    load_config,
    register_config_model,
)


class SampleConfigModel(BaseModel):
    """Sample configuration model for testing."""

    test_string: str = "default"
    test_int: int = 42
    test_bool: bool = True


class SampleNestedConfigModel(BaseModel):
    """Sample nested configuration model for testing."""

    nested_string: str = "nested"
    nested_int: int = 100


class SampleComplexConfigModel(BaseModel):
    """Sample complex configuration model for testing."""

    complex_string: str = "complex"
    complex_int: int = 200
    nested: SampleNestedConfigModel = SampleNestedConfigModel()


def test_config_manager_init():
    """Test ConfigManager initialization."""
    # Default initialization
    manager = ConfigManager()
    assert manager.config_dir.endswith("presets")

    # Custom initialization
    custom_dir = "/tmp/config"
    manager = ConfigManager(config_dir=custom_dir)
    assert manager.config_dir == custom_dir


def test_register_model():
    """Test registering configuration models."""
    manager = ConfigManager()

    # Register a model
    manager.register_model("test", SampleConfigModel)
    assert "test" in manager.model_registry
    assert manager.model_registry["test"] == SampleConfigModel

    # Register another model
    manager.register_model("complex", SampleComplexConfigModel)
    assert "complex" in manager.model_registry
    assert manager.model_registry["complex"] == SampleComplexConfigModel


def test_load_config():
    """Test loading configuration from a file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create a test YAML config
        yaml_path = os.path.join(temp_dir, "test.yaml")
        with open(yaml_path, "w") as f:
            f.write(
                """
            test:
              test_string: "yaml_value"
              test_int: 123
            complex:
              complex_string: "complex_value"
              complex_int: 456
              nested:
                nested_string: "nested_value"
                nested_int: 789
            """
            )

        # Create a test JSON config
        json_path = os.path.join(temp_dir, "test.json")
        with open(json_path, "w") as f:
            f.write(
                """
            {
                "test": {
                    "test_string": "json_value",
                    "test_int": 321
                }
            }
            """
            )

        # Load YAML config
        manager = ConfigManager()
        config = manager.load_config(yaml_path, ConfigFormat.YAML)
        assert config["test"]["test_string"] == "yaml_value"
        assert config["test"]["test_int"] == 123
        assert config["complex"]["complex_string"] == "complex_value"
        assert config["complex"]["nested"]["nested_string"] == "nested_value"

        # Load JSON config
        config = manager.load_config(json_path, ConfigFormat.JSON)
        assert config["test"]["test_string"] == "json_value"
        assert config["test"]["test_int"] == 321

        # Test loading non-existent file
        with pytest.raises(FileNotFoundError):
            manager.load_config(os.path.join(temp_dir, "nonexistent.yaml"))


def test_validate_config():
    """Test validating configuration against models."""
    manager = ConfigManager()

    # Register models
    manager.register_model("test", SampleConfigModel)
    manager.register_model("complex", SampleComplexConfigModel)

    # Valid configuration
    valid_config = {
        "test": {"test_string": "valid", "test_int": 123, "test_bool": False},
        "complex": {
            "complex_string": "valid_complex",
            "complex_int": 456,
            "nested": {"nested_string": "valid_nested", "nested_int": 789},
        },
    }

    validated = manager.validate_config(valid_config)
    assert validated["test"]["test_string"] == "valid"
    assert validated["test"]["test_int"] == 123
    assert validated["test"]["test_bool"] is False
    assert validated["complex"]["complex_string"] == "valid_complex"
    assert validated["complex"]["nested"]["nested_string"] == "valid_nested"

    # Invalid configuration (wrong type)
    invalid_config = {
        "test": {
            "test_string": "valid",
            "test_int": "not_an_int",  # Should be an int
            "test_bool": False,
        }
    }

    with pytest.raises(ValueError):
        manager.validate_config(invalid_config)

    # Missing section (should use defaults)
    missing_section = {
        "test": {"test_string": "valid", "test_int": 123, "test_bool": False}
        # Missing "complex" section
    }

    validated = manager.validate_config(missing_section)
    assert validated["test"]["test_string"] == "valid"
    assert "complex" in validated
    assert validated["complex"]["complex_string"] == "complex"  # Default value
    assert validated["complex"]["nested"]["nested_string"] == "nested"  # Default value


def test_get_config():
    """Test getting configuration sections."""
    manager = ConfigManager()

    # Register models
    manager.register_model("test", SampleConfigModel)
    manager.register_model("complex", SampleComplexConfigModel)

    # Load a test config
    manager.configs["main"] = {
        "test": {"test_string": "get_test", "test_int": 123, "test_bool": False},
        "complex": {
            "complex_string": "get_complex",
            "complex_int": 456,
            "nested": {"nested_string": "get_nested", "nested_int": 789},
        },
    }

    # Get entire config
    config = manager.get_config()
    assert config["test"]["test_string"] == "get_test"
    assert config["complex"]["nested"]["nested_string"] == "get_nested"

    # Get section as dict
    test_section = manager.get_config("test")
    assert test_section["test_string"] == "get_test"
    assert test_section["test_int"] == 123

    # Get section as model
    test_model = manager.get_config("test", SampleConfigModel)
    assert isinstance(test_model, SampleConfigModel)
    assert test_model.test_string == "get_test"
    assert test_model.test_int == 123

    # Get complex section as model
    complex_model = manager.get_config("complex", SampleComplexConfigModel)
    assert isinstance(complex_model, SampleComplexConfigModel)
    assert complex_model.complex_string == "get_complex"
    assert complex_model.nested.nested_string == "get_nested"

    # Get non-existent section
    empty_section = manager.get_config("nonexistent")
    assert empty_section == {}

    # Get non-existent section as model
    empty_model = manager.get_config("nonexistent", SampleConfigModel)
    assert isinstance(empty_model, SampleConfigModel)
    assert empty_model.test_string == "default"  # Default value


def test_merge_configs():
    """Test merging configuration dictionaries."""
    manager = ConfigManager()

    base_config = {
        "test": {"test_string": "base", "test_int": 100, "test_bool": True},
        "base_only": {"value": "base_value"},
    }

    override_config = {
        "test": {
            "test_string": "override",
            "test_int": 200,
            # test_bool not specified, should keep base value
        },
        "override_only": {"value": "override_value"},
    }

    merged = manager.merge_configs(base_config, override_config)

    # Check merged values
    assert merged["test"]["test_string"] == "override"  # Overridden
    assert merged["test"]["test_int"] == 200  # Overridden
    assert merged["test"]["test_bool"] is True  # Kept from base
    assert merged["base_only"]["value"] == "base_value"  # Kept from base
    assert merged["override_only"]["value"] == "override_value"  # Added from override


def test_global_functions():
    """Test the global configuration functions."""
    # Create a test config file
    with tempfile.TemporaryDirectory() as temp_dir:
        config_path = os.path.join(temp_dir, "test.yaml")
        with open(config_path, "w") as f:
            f.write(
                """
            test:
              test_string: "global_test"
              test_int: 999
            """
            )

        # Register a model
        register_config_model("test", SampleConfigModel)

        # Load the config
        config = load_config(config_path)
        assert config["test"]["test_string"] == "global_test"

        # Get config
        test_config = get_config("test", SampleConfigModel)
        assert test_config.test_string == "global_test"
        assert test_config.test_int == 999
