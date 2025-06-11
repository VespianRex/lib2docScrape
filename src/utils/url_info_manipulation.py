from urllib.parse import parse_qsl, urlencode, urlunparse

from .factory import create_url_info
from .info import (
    URLInfo,
)

# It seems these methods were intended to be part of the URLInfo class or a utility class.
# For now, I'll assume they are methods of URLInfo and update them.
# If this file is meant to be standalone functions, the structure would be different.


class URLInfoManipulationMixin:  # Renamed to avoid conflict if URLInfo is imported
    # ... existing code ...

    def with_scheme(self, scheme: str) -> "URLInfo":
        """Create a new URLInfo instance with a different scheme."""
        if not self.is_valid or not self._normalized_parsed:
            # Consider raising an error or returning a new invalid URLInfo
            return create_url_info(
                self.raw_url, self.base_url
            )  # Re-create to maintain state

        try:
            parts = list(self._normalized_parsed)
            parts[0] = scheme  # Replace scheme
            new_url_str_no_frag = urlunparse(tuple(parts))
            # Preserve original fragment
            final_url_str = (
                f"{new_url_str_no_frag}#{self.fragment}"
                if self.fragment
                else new_url_str_no_frag
            )
            return create_url_info(final_url_str, base_url=self.base_url)
        except Exception as e:
            # self.logger.warning(f"Scheme change failed: {e}") # logger might not be available
            print(f"Warning: Scheme change failed: {e}")  # Temporary print
            return create_url_info(self.raw_url, self.base_url)  # Fallback

    def with_path(self, path: str) -> "URLInfo":
        """Create a new URLInfo instance with a different path."""
        if not self.is_valid or not self._normalized_parsed:
            return create_url_info(self.raw_url, self.base_url)

        try:
            parts = list(self._normalized_parsed)
            parts[2] = path if path.startswith("/") else f"/{path}"  # Replace path
            new_url_str_no_frag = urlunparse(tuple(parts))
            final_url_str = (
                f"{new_url_str_no_frag}#{self.fragment}"
                if self.fragment
                else new_url_str_no_frag
            )
            return create_url_info(final_url_str, base_url=self.base_url)
        except Exception as e:
            print(f"Warning: Path change failed: {e}")
            return create_url_info(self.raw_url, self.base_url)

    def with_query_params(self, params: dict) -> "URLInfo":
        """Create a new URLInfo instance with updated query parameters."""
        if not self.is_valid or not self._normalized_parsed:
            return create_url_info(self.raw_url, self.base_url)

        try:
            existing_params = dict(
                parse_qsl(self._normalized_parsed.query or "", keep_blank_values=True)
            )
            existing_params.update(params)
            new_query = urlencode(existing_params)

            parts = list(self._normalized_parsed)
            parts[4] = new_query  # Replace query
            new_url_str_no_frag = urlunparse(tuple(parts))
            final_url_str = (
                f"{new_url_str_no_frag}#{self.fragment}"
                if self.fragment
                else new_url_str_no_frag
            )
            return create_url_info(final_url_str, base_url=self.base_url)
        except Exception as e:
            print(f"Warning: Query param update failed: {e}")
            return create_url_info(self.raw_url, self.base_url)

    def without_query_params(self, param_names: list) -> "URLInfo":
        """Create a new URLInfo instance with specific query parameters removed."""
        if not self.is_valid or not self._normalized_parsed:
            return create_url_info(self.raw_url, self.base_url)

        try:
            existing_params = dict(
                parse_qsl(self._normalized_parsed.query or "", keep_blank_values=True)
            )
            for name in param_names:
                if name in existing_params:
                    del existing_params[name]
            new_query = urlencode(existing_params)

            parts = list(self._normalized_parsed)
            parts[4] = new_query  # Replace query
            new_url_str_no_frag = urlunparse(tuple(parts))
            final_url_str = (
                f"{new_url_str_no_frag}#{self.fragment}"
                if self.fragment
                else new_url_str_no_frag
            )
            return create_url_info(final_url_str, base_url=self.base_url)
        except Exception as e:
            print(f"Warning: Query param removal failed: {e}")
            return create_url_info(self.raw_url, self.base_url)

    # The join method in info.py already uses create_url_info.
    # This join method seems to be a duplicate or an older version.
    # For now, I will update it to use create_url_info as well.
    # The original join in info.py is:
    # def join(self, relative_url: str) -> 'URLInfo':
    #     if not self.is_valid:
    #         raise ValueError("Cannot join with an invalid base URL")
    #     base = self.normalized_url
    #     from .factory import create_url_info # Local import
    #     return create_url_info(relative_url, base_url=base)

    def join(
        self, path: str
    ) -> "URLInfo":  # Renamed relative_url to path for consistency
        """Join with a relative path and return a new URLInfo instance."""
        if not self.is_valid:
            # Consider raising ValueError as in the original info.py's join
            print("Warning: Joining with an invalid base URL.")
            return create_url_info(
                path, base_url=self.raw_url
            )  # Attempt with raw_url as base

        try:
            # The original join in info.py uses self.normalized_url as base.
            # This one seems to imply self.raw_url or self.url could be used.
            # Using self.normalized_url for consistency with the one in info.py.
            base_for_join = self.normalized_url

            # urljoin handles combining base and relative path correctly.
            # The create_url_info will then re-process this fully resolved URL.
            return create_url_info(path, base_url=base_for_join)
        except Exception as e:
            print(f"Warning: URL join failed: {e}")
            return create_url_info(path, base_url=self.raw_url)  # Fallback
