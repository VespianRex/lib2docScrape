#!/usr/bin/env python3
"""
Test GUI files without starting the server.
This tests the HTML templates and static files for correctness.
"""

import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GUIFilesTester:
    """Test GUI files for correctness."""

    def __init__(self):
        self.project_root = Path(__file__).parent

    def test_templates_exist(self) -> bool:
        """Test that all required templates exist."""
        templates_dir = self.project_root / "templates"
        required_templates = [
            "base.html",
            "scraping_dashboard.html",
            "index.html",
            "config.html",
            "results.html",
            "libraries.html",
        ]

        missing_templates = []
        for template in required_templates:
            template_path = templates_dir / template
            if not template_path.exists():
                missing_templates.append(template)

        if missing_templates:
            logger.error(f"❌ Missing templates: {missing_templates}")
            return False
        else:
            logger.info("✅ All required templates exist")
            return True

    def test_static_files_exist(self) -> bool:
        """Test that all required static files exist."""
        static_dir = self.project_root / "static"
        required_files = ["css/styles.css", "css/scraping_dashboard.css"]

        missing_files = []
        for file_path in required_files:
            full_path = static_dir / file_path
            if not full_path.exists():
                missing_files.append(file_path)

        if missing_files:
            logger.error(f"❌ Missing static files: {missing_files}")
            return False
        else:
            logger.info("✅ All required static files exist")
            return True

    def test_scraping_dashboard_content(self) -> bool:
        """Test that the scraping dashboard has all required elements."""
        template_path = self.project_root / "templates" / "scraping_dashboard.html"

        if not template_path.exists():
            logger.error("❌ scraping_dashboard.html not found")
            return False

        with open(template_path) as f:
            content = f.read()

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
            'id="benchmarkBtn"',
            'id="helpBtn"',
            'id="searchLibraryBtn"',
            'id="librarySearchResults"',
            'id="closeSearchResults"',
        ]

        missing_elements = []
        for element in required_elements:
            if element not in content:
                missing_elements.append(element)

        if missing_elements:
            logger.error(
                f"❌ Missing elements in scraping dashboard: {missing_elements}"
            )
            return False
        else:
            logger.info("✅ Scraping dashboard has all required elements")
            return True

    def test_javascript_functions(self) -> bool:
        """Test that required JavaScript functions are present."""
        template_path = self.project_root / "templates" / "scraping_dashboard.html"

        with open(template_path) as f:
            content = f.read()

        required_functions = [
            "updateConfigPreset",
            "updateBackendDescription",
            "initializeScrapingForm",
            "showErrorMessage",
            "showSuccessMessage",
            "showScrapingResults",
            "startBenchmark",
            "initializeAdvancedFeatures",
            "searchForLibraryDocs",
            "displayLibrarySearchResults",
            "selectLibraryUrl",
        ]

        missing_functions = []
        for func in required_functions:
            # Check for function definition or function call
            if f"function {func}" not in content and f"{func}(" not in content:
                missing_functions.append(func)

        if missing_functions:
            logger.error(f"❌ Missing JavaScript functions: {missing_functions}")
            return False
        else:
            logger.info("✅ All required JavaScript functions are present")
            return True

    def test_websocket_integration(self) -> bool:
        """Test that WebSocket integration is properly set up."""
        template_path = self.project_root / "templates" / "scraping_dashboard.html"

        with open(template_path) as f:
            content = f.read()

        websocket_elements = [
            "WebSocketManager",
            "/ws/scraping",
            "ws.on(",
            "scraping_progress",
            "metrics",
            "log",
        ]

        missing_elements = []
        for element in websocket_elements:
            if element not in content:
                missing_elements.append(element)

        if missing_elements:
            logger.error(f"❌ Missing WebSocket elements: {missing_elements}")
            return False
        else:
            logger.info("✅ WebSocket integration is properly set up")
            return True

    def test_base_template(self) -> bool:
        """Test that the base template has required structure."""
        template_path = self.project_root / "templates" / "base.html"

        with open(template_path) as f:
            content = f.read()

        required_elements = [
            "<!DOCTYPE html>",
            "WebSocketManager",
            "bootstrap",
            "{% block content %}",
            "{% block extra_js %}",
            "{% block extra_css %}",
        ]

        missing_elements = []
        for element in required_elements:
            if element not in content:
                missing_elements.append(element)

        if missing_elements:
            logger.error(f"❌ Missing elements in base template: {missing_elements}")
            return False
        else:
            logger.info("✅ Base template has required structure")
            return True

    def test_css_files(self) -> bool:
        """Test that CSS files have required styles."""
        css_files = [
            ("static/css/styles.css", ["loading-indicator", "progress-bar", "card"]),
            (
                "static/css/scraping_dashboard.css",
                ["log-viewer", "metrics-display", "progress-bar"],
            ),
        ]

        all_passed = True

        for css_file, required_classes in css_files:
            css_path = self.project_root / css_file

            if not css_path.exists():
                logger.error(f"❌ CSS file not found: {css_file}")
                all_passed = False
                continue

            with open(css_path) as f:
                content = f.read()

            missing_classes = []
            for css_class in required_classes:
                if css_class not in content:
                    missing_classes.append(css_class)

            if missing_classes:
                logger.error(f"❌ Missing CSS classes in {css_file}: {missing_classes}")
                all_passed = False
            else:
                logger.info(f"✅ CSS file {css_file} has required styles")

        return all_passed

    def run_all_tests(self) -> bool:
        """Run all GUI file tests."""
        logger.info("🚀 Starting GUI files tests...")

        tests = [
            ("Templates Exist", self.test_templates_exist),
            ("Static Files Exist", self.test_static_files_exist),
            ("Scraping Dashboard Content", self.test_scraping_dashboard_content),
            ("JavaScript Functions", self.test_javascript_functions),
            ("WebSocket Integration", self.test_websocket_integration),
            ("Base Template", self.test_base_template),
            ("CSS Files", self.test_css_files),
        ]

        passed_tests = 0
        total_tests = len(tests)

        for test_name, test_func in tests:
            logger.info(f"\n📋 Running {test_name} test...")
            if test_func():
                passed_tests += 1
            else:
                logger.error(f"❌ {test_name} test failed")

        logger.info(
            f"\n🏁 GUI Files Tests Complete: {passed_tests}/{total_tests} tests passed"
        )

        if passed_tests == total_tests:
            logger.info("🎉 All GUI file tests passed!")
            return True
        else:
            logger.error("❌ Some GUI file tests failed.")
            return False


def main():
    """Main function to run GUI file tests."""
    tester = GUIFilesTester()
    success = tester.run_all_tests()

    if success:
        print("\n✅ GUI files are correctly structured!")
        print("📁 All templates, static files, and JavaScript are in place")
        print("🚀 Ready to start the server and run integration tests")
        return 0
    else:
        print("\n❌ GUI file tests failed.")
        print("🔧 Please fix the issues above before running the server")
        return 1


if __name__ == "__main__":
    exit(main())
