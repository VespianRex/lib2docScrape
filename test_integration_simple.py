#!/usr/bin/env python3
"""
Simple integration test script to verify GUI functionality.
This script tests the backend API endpoints without complex imports.
"""

import logging

import requests

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SimpleIntegrationTester:
    """Simple integration tester for the GUI and backend."""

    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 10

    def test_server_running(self) -> bool:
        """Test if the server is running."""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code == 200:
                logger.info("✅ Server is running and accessible")
                return True
            else:
                logger.error(f"❌ Server returned status code: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            logger.error("❌ Cannot connect to server. Is it running?")
            logger.info("💡 Start the server with: python start_server.py")
            return False
        except Exception as e:
            logger.error(f"❌ Error connecting to server: {e}")
            return False

    def test_home_page(self) -> bool:
        """Test that the home page loads correctly."""
        try:
            response = self.session.get(f"{self.base_url}/")
            if response.status_code != 200:
                logger.error(f"❌ Home page returned status {response.status_code}")
                return False

            content = response.text
            required_elements = [
                "Documentation Scraping Dashboard",
                'id="docUrl"',
                'id="backend"',
                'id="start-scraping-button"',
            ]

            missing_elements = []
            for element in required_elements:
                if element not in content:
                    missing_elements.append(element)

            if missing_elements:
                logger.error(f"❌ Missing elements in home page: {missing_elements}")
                return False
            else:
                logger.info("✅ Home page loads correctly with all required elements")
                return True

        except Exception as e:
            logger.error(f"❌ Home page test failed: {e}")
            return False

    def test_api_endpoints(self) -> bool:
        """Test all API endpoints."""
        tests_passed = 0
        total_tests = 0

        endpoints = [
            ("/api/scraping/status", "GET", "Scraping status"),
            ("/api/scraping/backends", "GET", "Available backends"),
            ("/api/scraping/results", "GET", "Scraping results"),
        ]

        for endpoint, method, description in endpoints:
            total_tests += 1
            try:
                if method == "GET":
                    response = self.session.get(f"{self.base_url}{endpoint}")
                else:
                    response = self.session.post(f"{self.base_url}{endpoint}")

                if response.status_code == 200:
                    logger.info(f"✅ {description} endpoint works")
                    tests_passed += 1
                else:
                    logger.error(
                        f"❌ {description} endpoint returned {response.status_code}"
                    )

            except Exception as e:
                logger.error(f"❌ {description} endpoint test failed: {e}")

        # Test POST endpoints with data
        post_tests = [
            ("/api/benchmark/start", {"url": "https://example.com"}, "Benchmark start"),
        ]

        for endpoint, data, description in post_tests:
            total_tests += 1
            try:
                response = self.session.post(
                    f"{self.base_url}{endpoint}",
                    json=data,
                    headers={"Content-Type": "application/json"},
                )

                if response.status_code in [200, 201]:
                    logger.info(f"✅ {description} endpoint works")
                    tests_passed += 1
                else:
                    logger.error(
                        f"❌ {description} endpoint returned {response.status_code}"
                    )

            except Exception as e:
                logger.error(f"❌ {description} endpoint test failed: {e}")

        logger.info(f"API Tests: {tests_passed}/{total_tests} passed")
        return tests_passed == total_tests

    def test_static_files(self) -> bool:
        """Test that static files are accessible."""
        tests_passed = 0
        total_tests = 0

        static_files = ["/static/css/styles.css", "/static/css/scraping_dashboard.css"]

        for file_path in static_files:
            total_tests += 1
            try:
                response = self.session.get(f"{self.base_url}{file_path}")
                if response.status_code == 200:
                    logger.info(f"✅ Static file accessible: {file_path}")
                    tests_passed += 1
                else:
                    logger.error(
                        f"❌ Static file {file_path} returned {response.status_code}"
                    )
            except Exception as e:
                logger.error(f"❌ Static file test failed for {file_path}: {e}")

        logger.info(f"Static Files Tests: {tests_passed}/{total_tests} passed")
        return tests_passed == total_tests

    def test_javascript_functionality(self) -> bool:
        """Test that JavaScript functions are present in the page."""
        try:
            response = self.session.get(f"{self.base_url}/")
            content = response.text

            required_functions = [
                "updateConfigPreset",
                "updateBackendDescription",
                "initializeScrapingForm",
                "showErrorMessage",
                "showSuccessMessage",
            ]

            missing_functions = []
            for func in required_functions:
                if f"function {func}" not in content and f"{func}(" not in content:
                    missing_functions.append(func)

            if missing_functions:
                logger.error(f"❌ Missing JavaScript functions: {missing_functions}")
                return False
            else:
                logger.info("✅ All required JavaScript functions are present")
                return True

        except Exception as e:
            logger.error(f"❌ JavaScript functionality test failed: {e}")
            return False

    def test_websocket_endpoint(self) -> bool:
        """Test that WebSocket endpoint is accessible."""
        try:
            # We can't easily test WebSocket with requests, but we can check if the endpoint exists
            # by looking for WebSocket-related code in the page
            response = self.session.get(f"{self.base_url}/")
            content = response.text

            websocket_indicators = ["WebSocketManager", "/ws/scraping", "websocket"]

            found_indicators = []
            for indicator in websocket_indicators:
                if indicator in content:
                    found_indicators.append(indicator)

            if len(found_indicators) >= 2:
                logger.info("✅ WebSocket functionality appears to be implemented")
                return True
            else:
                logger.error(
                    f"❌ WebSocket functionality may be missing. Found: {found_indicators}"
                )
                return False

        except Exception as e:
            logger.error(f"❌ WebSocket test failed: {e}")
            return False

    def run_all_tests(self) -> bool:
        """Run all integration tests."""
        logger.info("🚀 Starting simple integration tests...")

        # First check if server is running
        if not self.test_server_running():
            return False

        tests = [
            ("Home Page", self.test_home_page),
            ("API Endpoints", self.test_api_endpoints),
            ("Static Files", self.test_static_files),
            ("JavaScript Functionality", self.test_javascript_functionality),
            ("WebSocket Support", self.test_websocket_endpoint),
        ]

        passed_tests = 0
        total_tests = len(tests)

        for test_name, test_func in tests:
            logger.info(f"\n📋 Running {test_name} tests...")
            if test_func():
                passed_tests += 1
            else:
                logger.error(f"❌ {test_name} tests failed")

        logger.info(
            f"\n🏁 Integration Tests Complete: {passed_tests}/{total_tests} test suites passed"
        )

        if passed_tests == total_tests:
            logger.info("🎉 All tests passed! The GUI is working correctly.")
            return True
        else:
            logger.error("❌ Some tests failed. Please check the issues above.")
            return False


def main():
    """Main function to run integration tests."""
    tester = SimpleIntegrationTester()
    success = tester.run_all_tests()

    if success:
        print("\n✅ Integration tests passed! Your GUI is ready to use.")
        print("🌐 Access the GUI at: http://localhost:8000")
        print("📖 See GUI_README.md for detailed feature documentation")
        return 0
    else:
        print("\n❌ Integration tests failed.")
        print("💡 Make sure the server is running: python start_server.py")
        print("🔧 Check the error messages above for specific issues")
        return 1


if __name__ == "__main__":
    exit(main())
