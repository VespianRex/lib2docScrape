# Add these improvements to URLInfo class

class URLInfo:
    # ... existing code ...
    
    # Add class-level LRU cache for common operations
    @classmethod
    @functools.lru_cache(maxsize=1024)
    def from_cache(cls, url: str, base_url: Optional[str] = None) -> 'URLInfo':
        """Factory method that caches URLInfo instances for performance."""
        return cls(url, base_url)
    
    @staticmethod
    @functools.lru_cache(maxsize=256)
    def _is_default_port(scheme: str, port: int) -> bool:
        """Check if a port is the default for a scheme (with caching)."""
        default_ports = {
            'http': 80,
            'https': 443,
            'ftp': 21,
            'ftps': 990,
        }
        return scheme in default_ports and port == default_ports[scheme]
    
    @staticmethod
    @functools.lru_cache(maxsize=1024)
    def _normalize_hostname_cached(hostname: str) -> str:
        """Cached version of hostname normalization."""
        return URLInfo._normalize_hostname(hostname)