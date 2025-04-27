import pytest
from src.utils.url import URLInfo

class TestURLSecurityExtra:
    """Test additional security edge cases for URL handling."""

    @pytest.mark.parametrize("url, expected_valid, description", [
        # Path traversal attempts (more variations)
        ("https://example.com/../secret", False, "Path traversal up one level"),
        ("https://example.com/docs/../../etc/passwd", False, "Path traversal up multiple levels"),
        ("https://example.com/%2e%2e/secret", False, "URL encoded path traversal"),
        ("https://example.com/..%2fsecret", False, "Mixed encoding path traversal"),
        ("https://example.com/..\\secret", False, "Backslash path traversal"), # Common on Windows

        # Scheme exploitation attempts
        ("ftp://example.com/resource", False, "Disallowed scheme: FTP"),
        ("smb://example.com/share", False, "Disallowed scheme: SMB"),
        ("file:///etc/passwd", False, "Disallowed scheme: local file access"),
        ("javascript:void(0)", False, "Javascript URI scheme"), # Already covered, but good to re-affirm
        ("vbscript:msgbox('XSS')", False, "VBScript URI scheme"),

        # Server-Side Request Forgery (SSRF) attempts (basic checks)
        ("http://localhost/admin", False, "SSRF attempt to localhost"),
        ("http://127.0.0.1/secrets", False, "SSRF attempt to loopback IP"),
        ("http://169.254.169.254/latest/meta-data/", False, "SSRF attempt to AWS metadata service"),
        ("http://metadata.google.internal/computeMetadata/v1/", False, "SSRF attempt to GCP metadata service"),

        # Homograph attacks (using visually similar characters - basic check)
        # Note: Full homograph detection is complex. This checks for obviously problematic schemes.
        # A more robust check might involve IDNA processing and character analysis.
        ("http://еxample.com", True, "Cyrillic 'е' instead of Latin 'e' - Should ideally be handled by IDNA normalization, but basic validation passes"), # This might pass basic validation but fail normalization/comparison
        ("https://google.com@evil.com/", False, "URL with username/password attempting to mask domain"),

        # Extremely long URLs (potential DoS vector)
        ("https://example.com/" + "a" * 3000, False, "Excessively long URL path"),

        # Control characters in URL
        ("https://example.com/page\nnewline", False, "Newline character in URL"),
        ("https://example.com/page\t tab", False, "Tab character in URL"),
    ])
    def test_various_security_risks(self, url, expected_valid, description):
        """Test URLInfo against various security risk patterns."""
        info = URLInfo(url)
        assert info.is_valid == expected_valid, f"Failed check: {description} ({url})"
        if not expected_valid:
            assert info.error_message is not None, f"Error message expected for invalid URL: {description} ({url})"