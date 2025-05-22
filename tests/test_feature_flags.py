import time
import json
import pytest
from pathlib import Path
from src.utils.feature_flags import FeatureFlags

@pytest.fixture
def sample_flags_file(tmp_path):
    """Create a sample feature flags config file"""
    config = {
        "feature_flags": {
            "test_flag": {
                "enabled": True,
                "description": "Test flag"
            }
        }
    }
    
    config_file = tmp_path / "test_config.json"
    with open(config_file, 'w') as f:
        json.dump(config, f)
        
    return config_file

def test_file_watcher(sample_flags_file):
    """Test auto-reload when config file changes"""
    flags = FeatureFlags(sample_flags_file)
    
    # Initial state
    assert flags.is_enabled("test_flag")
    
    # Modify configuration file
    new_config = {
        "feature_flags": {
            "test_flag": {
                "enabled": False,
                "description": "Modified flag"
            }
        }
    }
    
    with open(sample_flags_file, 'w') as f:
        json.dump(new_config, f)
    
    # Allow time for file watch event
    time.sleep(0.1)
    
    # Check auto-reload worked
    assert not flags.is_enabled("test_flag")
    assert flags.get_description("test_flag") == "Modified flag"