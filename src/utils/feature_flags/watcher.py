from pathlib import Path
from typing import Callable

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class ConfigFileHandler(FileSystemEventHandler):
    def __init__(self, callback: Callable[[], None]):
        self.callback = callback

    def on_modified(self, event):
        if not event.is_directory:
            self.callback()


class FeatureFlagWatcher:
    def __init__(self, config_path: Path, reload_callback: Callable[[], None]):
        self.path = config_path
        self.callback = reload_callback
        self.observer = Observer()

    def start(self):
        """Start watching config file"""
        event_handler = ConfigFileHandler(self.callback)
        self.observer.schedule(event_handler, str(self.path.parent), recursive=False)
        self.observer.start()

    def stop(self):
        """Stop watching config file"""
        self.observer.stop()
        self.observer.join()
