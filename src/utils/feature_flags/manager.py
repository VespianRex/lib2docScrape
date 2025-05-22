from pathlib import Path
from typing import Optional, Dict, Any
from .config import FeatureFlagConfig
from .watcher import FeatureFlagWatcher

class FeatureFlags:
    def __init__(self, config_path: Path):
        self.config = FeatureFlagConfig(config_path)
        self._flags: Dict[str, Any] = {}
        self._watcher = FeatureFlagWatcher(config_path, self._reload_config)
        self._watcher.start()
        self._reload_config()  # Load initial config

    def _reload_config(self):
        """Reload configuration from file"""
        self._flags = self.config.load().get("feature_flags", {})
        
    def is_enabled(self, flag_name: str) -> bool:
        """Check if a feature flag is enabled"""
        return self._flags.get(flag_name, {}).get("enabled", False)
    
    def get_description(self, flag_name: str) -> Optional[str]:
        """Get feature flag description"""
        return self._flags.get(flag_name, {}).get("description")