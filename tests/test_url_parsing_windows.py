import pytest
from src.utils.url.factory import create_url_info # Import the factory function
from src.utils.url import URLInfo # Keep URLInfo import for type hinting if needed elsewhere
from src.utils.url.types import URLType  # Import URLType for the test

class TestURLParsingWindows:
    """Test URL parsing edge cases related to Windows-style paths."""

    @pytest.mark.parametrize("input_url, base_url, expected_normalized_url, description", [
        # Basic Windows path (should be treated as relative path if no scheme)
        # Assuming the URL parser correctly handles this or identifies it as invalid/relative.
        # The behavior might depend heavily on the base URL context.
        ("C:\\Users\\User\\Documents\\file.html", "https://example.com/docs/", None, "Absolute Windows path without scheme"), # Expect invalid or needs base
        # UNC path resolved relative to base - this is valid behavior
        ("\\\\server\\share\\file.txt", "https://example.com/docs/", "https://example.com/docs/server/share/file.txt", "UNC path resolved relative to base"),

        # Windows path misinterpreted as host or path segments
        # This depends on how urlparse/urljoin handles backslashes.
        # Standard libraries often treat backslashes differently than forward slashes.
        ("https://example.com/path\\to\\resource", "https://example.com", "https://example.com/path/to/resource", "Backslashes in path segment"), # Should normalize

        # File scheme with Windows paths - now allowed
        ("file:///C:/Users/User/Documents/file.html", None, "file:///C:/Users/User/Documents/file.html", "File scheme with absolute Windows path - now allowed"),
        # Note: File scheme is now allowed

        # Relative Windows paths (relative to a base URL)
        ("subfolder\\file.html", "https://example.com/docs/", "https://example.com/docs/subfolder/file.html", "Relative path with backslashes"),
        ("..\\other\\file.html", "https://example.com/docs/folder/", None, "Relative path traversal with backslashes (should be invalid)"), # Expect invalid due to traversal check
    ])
    def test_windows_path_handling(self, input_url, base_url, expected_normalized_url, description):
        """Test how Windows-style paths are handled during URL parsing and normalization."""
        # Use the factory function to create the URLInfo instance
        info = create_url_info(input_url, base_url=base_url)

        if "(should be invalid)" in description: # Check description for expected invalidity
            assert not info.is_valid, f"URL should be invalid: {description} ({input_url})"
            assert info.error_message is not None and "Path traversal attempt detected" in info.error_message, f"Incorrect error for {input_url}: {info.error_message}"
        elif expected_normalized_url is None:
             # If we expect it to be invalid or unresolvable for other reasons (like absolute Windows path without base)
             assert not info.is_valid or info.url_type == URLType.UNKNOWN, f"Expected invalid or unknown: {description} ({input_url})"
        else:
            # If we expect it to be valid (including the resolved UNC path)
            assert info.is_valid, f"URL should be valid: {description} ({input_url})"
            assert info.normalized_url == expected_normalized_url, f"Normalization failed: {description} ({input_url})"

    # Test case for potential misinterpretation if not handled carefully
    def test_windows_drive_as_scheme_or_host(self):
        """Test if 'C:' is misinterpreted."""
        # This depends heavily on the parser's leniency.
        # A strict parser should reject this if 'c' isn't a registered scheme.
        # Use the factory function
        info = create_url_info("C:file.html")
        # Expect urlparse to initially see 'c' as scheme, but our validation should catch it.
        assert not info.is_valid, "URL with 'C:' as scheme should be invalid"
        assert info.error_message is not None and 'Invalid scheme' in info.error_message, "Error message should indicate invalid scheme"
        # assert info.scheme is None or info.scheme.lower() != 'c', "'C:' should not be parsed as a scheme" # This fails as urlparse *does* parse it
        # assert not info.is_valid or info.url_type == URLType.RELATIVE, "Should be relative or invalid" # This part is correct