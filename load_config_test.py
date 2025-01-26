from src.main import load_config

config_path = 'config.yaml'

try:
    config = load_config(config_path)
    print("Config loaded successfully!")
    print(config)
except Exception as e:
    print(f"Error loading config: {e}")