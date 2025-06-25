#!/usr/bin/env python3
"""
Simple startup script for the Lib2DocScrape GUI.
"""

import logging
import sys
import webbrowser

import uvicorn

# Add src to path
sys.path.append("src")


def main():
    """Start the server and optionally open browser."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    print("🚀 Starting Lib2DocScrape GUI Server...")
    print("📍 Server will be available at: http://localhost:8000")
    print("🔧 Press Ctrl+C to stop the server")

    # Check if we should open browser
    open_browser = "--no-browser" not in sys.argv

    if open_browser:
        print("🌐 Opening browser in 3 seconds...")
        import threading
        import time

        def open_browser_delayed():
            time.sleep(3)
            try:
                webbrowser.open("http://localhost:8000")
            except Exception as e:
                logger.warning(f"Could not open browser: {e}")

        threading.Thread(target=open_browser_delayed, daemon=True).start()

    try:
        # Import the app
        from main import app

        # Start the server
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info", reload=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting server: {e}")
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
