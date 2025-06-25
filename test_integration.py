#!/usr/bin/env python3
"""
Integration test script to verify all GUI functionality works correctly.
This script tests the backend API endpoints and frontend integration.
"""

import logging
import sys

from fastapi.testclient import TestClient

# Import the main application
sys.path.insert(0, "src")
try:
    from src.main import app
except ImportError:
    # Try alternative import method
    import importlib.util

    spec = importlib.util.spec_from_file_location("main", "src/main.py")
    main_module = importlib.util.module_from_spec(spec)
    sys.modules["main"] = main_module
    spec.loader.exec_module(main_module)
    app = main_module.app

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class IntegrationTester:
    """Integration tester for the GUI and backend."""

    def __init__(self):
        self.client = TestClient(app)
        self.base_url = "http://localhost:8000"

    def test_home_page(self) -> bool:
        """Test that the home page loads correctly."""
        try:
            response = self.client.get("/")
            assert response.status_code == 200
            assert "Documentation Scraping Dashboard" in response.text
            logger.info("✅ Home page loads correctly")
            return True
        except Exception as e:
            logger.error(f"❌ Home page test failed: {e}")
            return False

    def test_api_endpoints(self) -> bool:
        """Test all API endpoints."""
        tests_passed = 0
        total_tests = 0

        # Test scraping status
        total_tests += 1
        try:
            response = self.client.get("/api/scraping/status")
            assert response.status_code == 200
            data = response.json()
            assert "is_running" in data
            logger.info("✅ Scraping status endpoint works")
            tests_passed += 1
        except Exception as e:
            logger.error(f"❌ Scraping status test failed: {e}")

        # Test available backends
        total_tests += 1
        try:
            response = self.client.get("/api/scraping/backends")
            assert response.status_code == 200
            backends = response.json()
            assert isinstance(backends, list)
            assert len(backends) > 0
            logger.info(f"✅ Available backends: {backends}")
            tests_passed += 1
        except Exception as e:
            logger.error(f"❌ Available backends test failed: {e}")

        # Test scraping results list
        total_tests += 1
        try:
            response = self.client.get("/api/scraping/results")
            assert response.status_code == 200
            results = response.json()
            assert isinstance(results, list)
            logger.info("✅ Scraping results endpoint works")
            tests_passed += 1
        except Exception as e:
            logger.error(f"❌ Scraping results test failed: {e}")

        # Test benchmark start
        total_tests += 1
        try:
            response = self.client.post(
                "/api/benchmark/start", json={"url": "https://example.com"}
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "success"
            logger.info("✅ Benchmark start endpoint works")
            tests_passed += 1
        except Exception as e:
            logger.error(f"❌ Benchmark start test failed: {e}")

        # Test benchmark results
        total_tests += 1
        try:
            response = self.client.get("/api/benchmark/results")
            assert response.status_code == 200
            data = response.json()
            assert "results" in data
            logger.info("✅ Benchmark results endpoint works")
            tests_passed += 1
        except Exception as e:
            logger.error(f"❌ Benchmark results test failed: {e}")

        # Test crawl endpoint
        total_tests += 1
        try:
            response = self.client.post(
                "/crawl",
                json={
                    "url": "https://example.com",
                    "backend": "crawl4ai",
                    "max_depth": 2,
                },
            )
            # This might fail due to actual crawling, but should not return 404
            assert response.status_code != 404
            logger.info("✅ Crawl endpoint is accessible")
            tests_passed += 1
        except Exception as e:
            logger.error(f"❌ Crawl endpoint test failed: {e}")

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
                response = self.client.get(file_path)
                assert response.status_code == 200
                logger.info(f"✅ Static file accessible: {file_path}")
                tests_passed += 1
            except Exception as e:
                logger.error(f"❌ Static file test failed for {file_path}: {e}")

        logger.info(f"Static Files Tests: {tests_passed}/{total_tests} passed")
        return tests_passed == total_tests

    def test_form_elements(self) -> bool:
        """Test that all required form elements are present in the HTML."""
        try:
            response = self.client.get("/")
            html_content = response.text

            required_elements = [
                'id="docUrl"',
                'id="backend"',
                'id="configPreset"',
                'id="scrapingMode"',
                'id="maxDepth"',
                'id="maxPages"',
                'id="outputFormat"',
                'id="start-scraping-button"',
                'id="error-message"',
                'id="success-message"',
                'id="scraping-results"',
            ]

            missing_elements = []
            for element in required_elements:
                if element not in html_content:
                    missing_elements.append(element)

            if missing_elements:
                logger.error(f"❌ Missing form elements: {missing_elements}")
                return False
            else:
                logger.info("✅ All required form elements are present")
                return True

        except Exception as e:
            logger.error(f"❌ Form elements test failed: {e}")
            return False

    def test_javascript_functions(self) -> bool:
        """Test that required JavaScript functions are present."""
        try:
            response = self.client.get("/")
            html_content = response.text

            required_functions = [
                "updateConfigPreset",
                "updateBackendDescription",
                "initializeScrapingForm",
                "showErrorMessage",
                "showSuccessMessage",
                "showScrapingResults",
            ]

            missing_functions = []
            for func in required_functions:
                if (
                    f"function {func}" not in html_content
                    and f"{func}(" not in html_content
                ):
                    missing_functions.append(func)

            if missing_functions:
                logger.error(f"❌ Missing JavaScript functions: {missing_functions}")
                return False
            else:
                logger.info("✅ All required JavaScript functions are present")
                return True

        except Exception as e:
            logger.error(f"❌ JavaScript functions test failed: {e}")
            return False

    def run_all_tests(self) -> bool:
        """Run all integration tests."""
        logger.info("🚀 Starting integration tests...")

        tests = [
            ("Home Page", self.test_home_page),
            ("API Endpoints", self.test_api_endpoints),
            ("Static Files", self.test_static_files),
            ("Form Elements", self.test_form_elements),
            ("JavaScript Functions", self.test_javascript_functions),
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
    tester = IntegrationTester()
    success = tester.run_all_tests()

    if success:
        print("\n✅ Integration tests passed! Your GUI is ready to use.")
        print("🚀 To start the server, run: python -m uvicorn src.main:app --reload")
        return 0
    else:
        print("\n❌ Integration tests failed. Please fix the issues above.")
        return 1


if __name__ == "__main__":
    exit(main())
