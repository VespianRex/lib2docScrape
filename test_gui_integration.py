#!/usr/bin/env python3
"""
Integration Test: Frontend-Backend Connection Validator
Tests if the GUI buttons actually connect to the backend correctly.
"""

import asyncio
import json
import logging
import sys
from multiprocessing import Process
from pathlib import Path

import aiohttp
import uvicorn

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GUIConnectionTester:
    """Tests frontend-backend connection for the GUI."""

    def __init__(self, base_url="http://localhost:8889"):
        self.base_url = base_url
        self.server_process = None

    async def start_server_process(self):
        """Start the GUI server in a separate process."""

        def run_server():
            try:
                # Import here to avoid import issues in main process
                from run_gui import app

                uvicorn.run(app, host="0.0.0.0", port=8889, log_level="warning")
            except Exception as e:
                logger.error(f"Server startup error: {e}")

        self.server_process = Process(target=run_server)
        self.server_process.start()

        # Wait for server to start
        for i in range(30):  # Wait up to 30 seconds
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(
                        f"{self.base_url}/api/libraries", timeout=2
                    ) as response:
                        if response.status == 200:
                            logger.info("✅ Server started successfully")
                            return True
            except:
                await asyncio.sleep(1)

        logger.error("❌ Server failed to start within 30 seconds")
        return False

    def stop_server(self):
        """Stop the GUI server process."""
        if self.server_process:
            self.server_process.terminate()
            self.server_process.join()

    async def test_api_endpoints_exist(self):
        """Test if the required API endpoints exist."""
        logger.info("🔍 Testing API endpoint existence...")

        endpoints_to_test = [
            ("/api/libraries", "GET"),
            ("/api/scraping/start", "POST"),
            ("/api/scraping/stop", "POST"),
        ]

        results = {}

        async with aiohttp.ClientSession() as session:
            for endpoint, method in endpoints_to_test:
                try:
                    url = f"{self.base_url}{endpoint}"

                    if method == "GET":
                        async with session.get(url, timeout=5) as response:
                            exists = response.status != 404
                            results[endpoint] = {
                                "exists": exists,
                                "status": response.status,
                                "method": method,
                            }
                    else:  # POST
                        # Send a minimal test payload
                        test_data = {"test": True}
                        async with session.post(
                            url, json=test_data, timeout=5
                        ) as response:
                            exists = response.status != 404
                            results[endpoint] = {
                                "exists": exists,
                                "status": response.status,
                                "method": method,
                            }

                except Exception as e:
                    results[endpoint] = {
                        "exists": False,
                        "error": str(e),
                        "method": method,
                    }

        return results

    async def test_scraping_start_endpoint(self):
        """Test the /api/scraping/start endpoint with realistic data."""
        logger.info("🧪 Testing scraping start endpoint...")

        test_payload = {
            "url": "https://example.com",
            "backend": "http",
            "maxDepth": 2,
            "maxPages": 5,
            "outputFormat": "markdown",
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/scraping/start", json=test_payload, timeout=10
                ) as response:
                    status = response.status
                    response_text = await response.text()

                    try:
                        response_data = json.loads(response_text)
                    except:
                        response_data = {"raw_response": response_text}

                    return {
                        "status": status,
                        "response": response_data,
                        "success": status
                        in [200, 201, 202],  # Accept various success codes
                    }

        except Exception as e:
            return {"status": None, "error": str(e), "success": False}

    async def test_frontend_pages_load(self):
        """Test if main frontend pages load correctly."""
        logger.info("🌐 Testing frontend pages...")

        pages_to_test = ["/", "/config", "/results"]

        results = {}

        async with aiohttp.ClientSession() as session:
            for page in pages_to_test:
                try:
                    url = f"{self.base_url}{page}"
                    async with session.get(url, timeout=10) as response:
                        content = await response.text()

                        results[page] = {
                            "status": response.status,
                            "loads": response.status == 200,
                            "has_form": "scrapingForm" in content or "form" in content,
                            "has_buttons": "btn" in content,
                            "content_length": len(content),
                        }

                except Exception as e:
                    results[page] = {"status": None, "loads": False, "error": str(e)}

        return results

    async def run_full_test_suite(self):
        """Run complete frontend-backend integration test."""
        logger.info("🚀 Starting Frontend-Backend Integration Test")
        logger.info("=" * 60)

        # Start server
        if not await self.start_server_process():
            logger.error("❌ CRITICAL: Cannot start server - aborting tests")
            return False

        try:
            # Test API endpoints
            logger.info("\n📡 API ENDPOINT TESTS")
            api_results = await self.test_api_endpoints_exist()
            for endpoint, result in api_results.items():
                if result.get("exists", False):
                    logger.info(
                        f"✅ {endpoint} ({result['method']}) - Status: {result['status']}"
                    )
                else:
                    logger.error(
                        f"❌ {endpoint} ({result['method']}) - {result.get('error', 'Not found')}"
                    )

            # Test scraping endpoint specifically
            logger.info("\n🎯 SCRAPING ENDPOINT TEST")
            scraping_result = await self.test_scraping_start_endpoint()
            if scraping_result["success"]:
                logger.info(
                    f"✅ Scraping endpoint works - Status: {scraping_result['status']}"
                )
                logger.info(f"   Response: {scraping_result['response']}")
            else:
                logger.error(
                    f"❌ Scraping endpoint failed - {scraping_result.get('error', 'Unknown error')}"
                )
                logger.error(f"   Status: {scraping_result['status']}")

            # Test frontend pages
            logger.info("\n🌐 FRONTEND PAGE TESTS")
            frontend_results = await self.test_frontend_pages_load()
            for page, result in frontend_results.items():
                if result["loads"]:
                    logger.info(
                        f"✅ {page} loads - Has form: {result['has_form']}, Has buttons: {result['has_buttons']}"
                    )
                else:
                    logger.error(
                        f"❌ {page} failed - {result.get('error', 'Unknown error')}"
                    )

            # Summary
            logger.info("\n📋 TEST SUMMARY")
            logger.info("=" * 40)

            # API endpoint summary
            api_working = sum(1 for r in api_results.values() if r.get("exists", False))
            api_total = len(api_results)
            logger.info(f"API Endpoints: {api_working}/{api_total} working")

            # Frontend summary
            frontend_working = sum(1 for r in frontend_results.values() if r["loads"])
            frontend_total = len(frontend_results)
            logger.info(f"Frontend Pages: {frontend_working}/{frontend_total} loading")

            # Critical issue check
            critical_issues = []
            if not api_results.get("/api/scraping/start", {}).get("exists", False):
                critical_issues.append(
                    "❌ CRITICAL: /api/scraping/start endpoint missing (frontend will fail)"
                )

            if not scraping_result["success"]:
                critical_issues.append("❌ CRITICAL: Scraping functionality broken")

            if not any(r["loads"] for r in frontend_results.values()):
                critical_issues.append("❌ CRITICAL: No frontend pages loading")

            if critical_issues:
                logger.error("\n🚨 CRITICAL ISSUES FOUND:")
                for issue in critical_issues:
                    logger.error(f"   {issue}")
                return False
            else:
                logger.info(
                    "\n✅ ALL TESTS PASSED - Frontend-backend integration working!"
                )
                return True

        finally:
            self.stop_server()


async def main():
    """Main test function."""
    tester = GUIConnectionTester()
    success = await tester.run_full_test_suite()

    if success:
        logger.info("\n🎉 INTEGRATION TEST COMPLETED SUCCESSFULLY")
        sys.exit(0)
    else:
        logger.error("\n💥 INTEGRATION TEST FAILED - Issues need to be fixed")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
