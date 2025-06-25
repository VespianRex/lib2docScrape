#!/usr/bin/env python3
"""
Test server startup script that handles imports correctly.
"""

import logging
import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up logging
logging.basicConfig(level=logging.WARNING)


def start_server():
    """Start the server with proper import handling."""
    try:
        # Change to src directory and modify imports
        os.chdir("src")

        # Create a temporary main module with absolute imports
        main_content = """
import sys
import os
from pathlib import Path

# Add parent directory to path for absolute imports
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

# Now we can import with absolute paths
from src.backends.crawl4ai_backend import Crawl4AIBackend, Crawl4AIConfig
from src.backends.file_backend import FileBackend
from src.backends.lightpanda_backend import LightpandaBackend, LightpandaConfig
from src.backends.selector import BackendCriteria, BackendSelector
from src.benchmarking.backend_benchmark import BackendBenchmark
from src.crawler import CrawlerConfig, CrawlTarget, DocumentationCrawler
from src.organizers.doc_organizer import DocumentOrganizer, OrganizationConfig
from src.processors.content.models import ProcessorConfig as ProcessingConfig
from src.processors.content_processor import ContentProcessor
from src.processors.quality_checker import QualityChecker, QualityConfig
from src.utils.helpers import setup_logging

# Import the rest of main.py content
"""

        # Read the original main.py and modify imports
        with open("main.py") as f:
            original_content = f.read()

        # Replace relative imports with absolute imports
        modified_content = (
            original_content.replace(
                "from .backends.crawl4ai_backend import Crawl4AIBackend, Crawl4AIConfig",
                "# Import handled above",
            )
            .replace(
                "from .backends.file_backend import FileBackend",
                "# Import handled above",
            )
            .replace(
                "from .backends.lightpanda_backend import LightpandaBackend, LightpandaConfig",
                "# Import handled above",
            )
            .replace(
                "from .backends.selector import BackendCriteria, BackendSelector",
                "# Import handled above",
            )
            .replace(
                "from .benchmarking.backend_benchmark import BackendBenchmark",
                "# Import handled above",
            )
            .replace(
                "from .crawler import CrawlerConfig, CrawlTarget, DocumentationCrawler",
                "# Import handled above",
            )
            .replace(
                "from .organizers.doc_organizer import DocumentOrganizer, OrganizationConfig",
                "# Import handled above",
            )
            .replace(
                "from .processors.content.models import ProcessorConfig as ProcessingConfig",
                "# Import handled above",
            )
            .replace(
                "from .processors.content_processor import ContentProcessor",
                "# Import handled above",
            )
            .replace(
                "from .processors.quality_checker import QualityChecker, QualityConfig",
                "# Import handled above",
            )
            .replace(
                "from .utils.helpers import setup_logging", "# Import handled above"
            )
        )

        # Write the modified content to a temporary file
        with open("main_temp.py", "w") as f:
            f.write(main_content + modified_content)

        # Import and run
        import importlib.util

        import uvicorn

        spec = importlib.util.spec_from_file_location("main_temp", "main_temp.py")
        main_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(main_module)

        print("🚀 Starting test server on http://localhost:8000")
        uvicorn.run(main_module.app, host="127.0.0.1", port=8000, log_level="warning")

    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return False

    return True


if __name__ == "__main__":
    start_server()
