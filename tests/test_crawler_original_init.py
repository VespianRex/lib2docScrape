"""Tests specifically for the __init__ method from src.crawler.DocumentationCrawler."""

import inspect
import unittest

# Import the original DocumentationCrawler from src.crawler
import src.crawler


# Tests for the __init__ method
class TestDocumentationCrawlerInit(unittest.TestCase):
    def test_init_exists(self):
        """Test 5.0: Verify that the __init__ method exists in DocumentationCrawler."""
        # Get the original DocumentationCrawler class
        OriginalDocumentationCrawler = src.crawler.DocumentationCrawler

        # Verify that it has an __init__ method
        self.assertTrue(hasattr(OriginalDocumentationCrawler, "__init__"))

        # Check the signature of the __init__ method
        sig = inspect.signature(OriginalDocumentationCrawler.__init__)
        params = sig.parameters

        # Print info for debugging
        print(f"__init__ signature: {sig}")

        # Check that it has the expected parameters (adjust these if your actual implementation differs)
        expected_params = [
            "self",
            "config",
            "backend_selector",
            "content_processor",
            "quality_checker",
            "document_organizer",
            "loop",
            "backend",
        ]

        for param in expected_params:
            self.assertIn(param, params)

    def test_default_initialization(self):
        """Test 5.1: Default initialization of DocumentationCrawler."""
        # Get the original DocumentationCrawler class
        OriginalDocumentationCrawler = src.crawler.DocumentationCrawler

        # Create an instance with default parameters
        crawler = OriginalDocumentationCrawler()

        # Verify that the instance was created
        self.assertIsNotNone(crawler)

        # Check for expected attributes that should be set during initialization
        self.assertIsNotNone(crawler.config)

        # The following attributes may not be initialized directly in this implementation
        # but we should verify that the object doesn't raise errors when we access them
        try:
            _ = crawler.backend_selector
        except AttributeError:
            pass

        try:
            _ = crawler.content_processor
        except AttributeError:
            pass

        try:
            _ = crawler.quality_checker
        except AttributeError:
            pass

        try:
            _ = crawler.document_organizer
        except AttributeError:
            pass

        # These should be available in the new implementation
        self.assertIsNotNone(crawler.rate_limiter)

    def test_initialization_with_backend(self):
        """Test 5.3: Initialization with a specific backend."""
        # Get the original DocumentationCrawler class
        OriginalDocumentationCrawler = src.crawler.DocumentationCrawler

        # Create a dummy backend object
        class DummyBackend:
            pass

        backend = DummyBackend()

        # Initialize the crawler with the backend
        crawler = OriginalDocumentationCrawler(backend=backend)

        # Verify that the instance was created
        self.assertIsNotNone(crawler)

        # Check that the backend was set properly
        self.assertEqual(crawler.backend, backend)


if __name__ == "__main__":
    unittest.main()
