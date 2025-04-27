import pytest
from src.utils.url import URLInfo

class TestURLParsingWindows:
    """Test URL parsing edge cases related to Windows-style paths."""

    @pytest.mark.parametrize("input_url, base_url, expected_normalized_url, description", [
        # Basic Windows path (should be treated as relative path if no scheme)
        # Assuming the URL parser correctly handles this or identifies it as invalid/relative.
        # The behavior might depend heavily on the base URL context.
        ("C:\\Users\\User\\Documents\\file.html", "https://example.com/docs/", None, "Absolute Windows path without scheme"), # Expect invalid or needs base
        ("\\\\server\\share\\file.txt", "https://example.com/docs/", None, "UNC path without scheme"), # Expect invalid or needs base

        # Windows path misinterpreted as host or path segments
        # This depends on how urlparse/urljoin handles backslashes.
        # Standard libraries often treat backslashes differently than forward slashes.
        ("https://example.com/path\\to\\resource", "https://example.com", "https://example.com/path/to/resource", "Backslashes in path segment"), # Should normalize

        # File scheme with Windows paths
        ("file:///C:/Users/User/Documents/file.html", None, "file:///C:/Users/User/Documents/file.html", "File scheme with absolute Windows path"),
        # Note: Handling of file:// scheme might vary; some parsers normalize slashes.

        # Relative Windows paths (relative to a base URL)
        ("subfolder\\file.html", "https://example.com/docs/", "https://example.com/docs/subfolder/file.html", "Relative path with backslashes"),
        ("..\\other\\file.html", "https://example.com/docs/folder/", "https://example.com/docs/other/file.html", "Relative path traversal with backslashes"),
    ])
    def test_windows_path_handling(self, input_url, base_url, expected_normalized_url, description):
        """Test how Windows-style paths are handled during URL parsing and normalization."""
        info = URLInfo(input_url, base_url=base_url)

        if expected_normalized_url is None:
            # If we expect it to be invalid or unresolvable without a base
            assert not info.is_valid or info.url_type == URLType.RELATIVE, f"Expected invalid or relative: {description} ({input_url})"
        else:
            assert info.is_valid, f"URL should be valid: {description} ({input_url})"
            assert info.normalized_url == expected_normalized_url, f"Normalization failed: {description} ({input_url})"

    # Test case for potential misinterpretation if not handled carefully
    def test_windows_drive_as_scheme_or_host(self):
        """Test if 'C:' is misinterpreted."""
        # This depends heavily on the parser's leniency.
        # A strict parser should reject this if 'c' isn't a registered scheme.
        info = URLInfo("C:file.html")
        # Expect urlparse to initially see 'c' as scheme, but our validation should catch it.
        assert not info.is_valid, "URL with 'C:' as scheme should be invalid"
        assert info.error_message is not None and 'Invalid scheme' in info.error_message, "Error message should indicate invalid scheme"
        # assert info.scheme is None or info.scheme.lower() != 'c', "'C:' should not be parsed as a scheme" # This fails as urlparse *does* parse it
        # assert not info.is_valid or info.url_type == URLType.RELATIVE, "Should be relative or invalid" # This part is correct