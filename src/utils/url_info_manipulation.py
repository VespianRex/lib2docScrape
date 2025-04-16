class URLInfo:
    # ... existing code ...
    
    def with_scheme(self, scheme: str) -> 'URLInfo':
        """Create a new URLInfo instance with a different scheme."""
        if not self.is_valid or not self._normalized_parsed:
            return self
        
        try:
            parts = list(self._normalized_parsed)
            parts[0] = scheme  # Replace scheme
            new_url = urlunparse(tuple(parts))
            return URLInfo(new_url)
        except Exception as e:
            self.logger.warning(f"Scheme change failed: {e}")
            return self
    
    def with_path(self, path: str) -> 'URLInfo':
        """Create a new URLInfo instance with a different path."""
        if not self.is_valid or not self._normalized_parsed:
            return self
        
        try:
            parts = list(self._normalized_parsed)
            parts[2] = path if path.startswith('/') else f"/{path}"  # Replace path
            new_url = urlunparse(tuple(parts))
            return URLInfo(new_url)
        except Exception as e:
            self.logger.warning(f"Path change failed: {e}")
            return self
    
    def with_query_params(self, params: dict) -> 'URLInfo':
        """Create a new URLInfo instance with updated query parameters."""
        if not self.is_valid or not self._normalized_parsed:
            return self
        
        try:
            # Get existing params
            existing_params = dict(parse_qsl(self._normalized_parsed.query, keep_blank_values=True))
            # Update with new params
            existing_params.update(params)
            # Create new query string
            new_query = urlencode(existing_params)
            
            parts = list(self._normalized_parsed)
            parts[4] = new_query  # Replace query
            new_url = urlunparse(tuple(parts))
            return URLInfo(new_url)
        except Exception as e:
            self.logger.warning(f"Query param update failed: {e}")
            return self
    
    def without_query_params(self, param_names: list) -> 'URLInfo':
        """Create a new URLInfo instance with specific query parameters removed."""
        if not self.is_valid or not self._normalized_parsed:
            return self
        
        try:
            # Get existing params
            existing_params = dict(parse_qsl(self._normalized_parsed.query, keep_blank_values=True))
            # Remove specified params
            for name in param_names:
                if name in existing_params:
                    del existing_params[name]
            # Create new query string
            new_query = urlencode(existing_params)
            
            parts = list(self._normalized_parsed)
            parts[4] = new_query  # Replace query
            new_url = urlunparse(tuple(parts))
            return URLInfo(new_url)
        except Exception as e:
            self.logger.warning(f"Query param removal failed: {e}")
            return self
    
    def join(self, path: str) -> 'URLInfo':
        """Join with a relative path and return a new URLInfo instance."""
        if not self.is_valid:
            return self
        
        try:
            joined_url = urljoin(self.normalized_url, path)
            return URLInfo(joined_url)
        except Exception as e:
            self.logger.warning(f"URL join failed: {e}")
            return self