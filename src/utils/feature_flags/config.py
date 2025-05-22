import json
from pathlib import Path
from typing import Dict, Any

class FeatureFlagConfig:
    def __init__(self, config_path: Path):
        self.config_path = config_path
        self._config = None

    def load(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(self.config_path) as f:
                config = json.load(f)
                if self.validate(config):
                    self._config = config
                    return config
                raise ValueError("Invalid configuration format")
        except (json.JSONDecodeError, OSError) as e:
            raise ValueError(f"Error loading configuration: {e}")

    def validate(self, config: Dict[str, Any]) -> bool:
        """Validate configuration format"""
        if not isinstance(config, dict):
            return False
        
        feature_flags = config.get("feature_flags")
        if not isinstance(feature_flags, dict):
            return False

        for flag_name, flag_data in feature_flags.items():
            if not isinstance(flag_data, dict):
                return False
            if "enabled" not in flag_data:
                return False
                
        return True