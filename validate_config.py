import yaml
from src.main import AppConfig

config_path = 'config.yaml'

with open(config_path, 'r') as f:
    config_data = yaml.safe_load(f)

try:
    AppConfig(**config_data)
    print("Config validation successful!")
except Exception as e:
    print(f"Config validation error: {e}")