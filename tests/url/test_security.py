"""
Tests for the URL security configuration.
"""

import pytest
import re
from src.utils.url.security import URLSecurityConfig

def test_security_config_constants():
    """Test the security configuration constants."""
    # Test allowed schemes
    assert 'http' in URLSecurityConfig.ALLOWED_SCHEMES
    assert 'https' in URLSecurityConfig.ALLOWED_SCHEMES
    assert 'file' in URLSecurityConfig.ALLOWED_SCHEMES
    assert 'ftp' in URLSecurityConfig.ALLOWED_SCHEMES
    
    # Test length limits
    assert URLSecurityConfig.MAX_PATH_LENGTH == 2048
    assert URLSecurityConfig.MAX_QUERY_LENGTH == 2048
    
    # Test default ports
    assert URLSecurityConfig.DEFAULT_PORTS['http'] == 80
    assert URLSecurityConfig.DEFAULT_PORTS['https'] == 443
    assert URLSecurityConfig.DEFAULT_PORTS['ftp'] == 21

def test_security_regex_patterns():
    """Test the regex patterns in security configuration."""
    # Test invalid chars pattern
    assert URLSecurityConfig.INVALID_CHARS.search('<script>')
    assert URLSecurityConfig.INVALID_CHARS.search('abc"def')
    assert not URLSecurityConfig.INVALID_CHARS.search('abcdef')
    
    # Test XSS pattern
    assert URLSecurityConfig.XSS_PATTERNS.search('javascript:alert(1)')
    assert URLSecurityConfig.XSS_PATTERNS.search('<script>alert(1)</script>')
    assert URLSecurityConfig.XSS_PATTERNS.search('onerror=alert(1)')
    assert not URLSecurityConfig.XSS_PATTERNS.search('normal text')
    
    # Test SQL injection pattern
    assert URLSecurityConfig.SQLI_PATTERNS.search("' OR '1'='1")
    assert URLSecurityConfig.SQLI_PATTERNS.search("UNION SELECT * FROM users")
    assert not URLSecurityConfig.SQLI_PATTERNS.search("normal query")
    
    # Test path traversal pattern
    assert URLSecurityConfig.INVALID_PATH_TRAVERSAL.search("/../")
    assert not URLSecurityConfig.INVALID_PATH_TRAVERSAL.search("/normal/path")
    
    # Test command injection pattern
    assert URLSecurityConfig.CMD_INJECTION_PATTERNS.search("cat file | grep pattern")
    assert URLSecurityConfig.CMD_INJECTION_PATTERNS.search("ls; rm -rf /")
    assert not URLSecurityConfig.CMD_INJECTION_PATTERNS.search("normal command")
    
    # Test null byte pattern
    assert URLSecurityConfig.NULL_BYTE_PATTERN.search("file%00.jpg")
    assert not URLSecurityConfig.NULL_BYTE_PATTERN.search("normal.jpg")
    
    # Test domain label pattern
    assert URLSecurityConfig.DOMAIN_LABEL_PATTERN.match("example")
    assert URLSecurityConfig.DOMAIN_LABEL_PATTERN.match("example-domain")
    assert not URLSecurityConfig.DOMAIN_LABEL_PATTERN.match("-example")
    assert not URLSecurityConfig.DOMAIN_LABEL_PATTERN.match("example-")