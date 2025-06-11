import functools
import ipaddress  # Import ipaddress for IP checking
import logging
from types import MappingProxyType  # Add this import
from typing import TYPE_CHECKING, Any, Callable, Optional
from urllib.parse import ParseResult, parse_qsl, urlunparse  # Removed unquote_plus

# Removed: validate_url, normalize_url, URLSecurityConfig, resolve_url, determine_url_type
from .domain_parser import extract_domain_parts  # Keep for domain_parts property

# Import necessary components
from .types import URLType

# Removed: from .url_info_manipulation import URLInfoManipulationMixin

if TYPE_CHECKING:
    pass  # For type hinting _creator_func


# Removed duplicate normalize_path and normalize_hostname functions

logger = logging.getLogger(__name__)


class URLInfo:  # Removed mixin inheritance
    """
    Represents processed URL information. Should be created via the `create_url_info` factory.
    Immutable after creation via the factory.
    """

    __slots__ = (
        "_raw_url",
        "base_url",
        "_parsed",  # Stores the result of urlparse on the *resolved* URL (before normalization)
        "_normalized_parsed",  # Stores the result of urlparse on the *normalized* URL
        "_normalized_url",  # Stores the normalized URL string (without fragment)
        "is_valid",  # Boolean indicating if the URL is considered valid after processing
        "error_message",  # Stores the reason for invalidity, if any
        "url_type",  # Enum indicating if the URL is INTERNAL, EXTERNAL, etc.
        "_original_path_had_trailing_slash",  # Flag for normalization logic
        "_original_fragment",  # Stores the original fragment identifier
        "_initialized",  # Internal flag set by the factory upon completion
        "_creator_func",  # Stores the function used to create URLInfo instances
        "__dict__",  # Needed for functools.cached_property
    )

    # Note: __init__ is intentionally simple.
    # Direct instantiation of URLInfo() creates an empty, non-functional object.
    # Use the factory function `create_url_info` from `src.utils.url.factory` instead.
    def __init__(
        self,
        raw_url: Optional[str] = None,
        normalized_url: Optional[str] = None,
        is_valid: bool = False,
        error_message: Optional[str] = None,
    ) -> None:
        """Initializes a URLInfo object. For test or factory use."""
        logger.debug("URLInfo __init__ called (factory or direct).")
        # Basic attributes initialization
        self._raw_url: str = raw_url or ""
        self.base_url: Optional[str] = None
        self._parsed: Optional[ParseResult] = None
        self._normalized_parsed: Optional[ParseResult] = None
        # normalized_url is stored without fragment
        self._normalized_url: Optional[str] = normalized_url
        self.is_valid: bool = is_valid
        self.error_message: Optional[str] = error_message
        self.url_type: URLType = URLType.UNKNOWN
        self._original_path_had_trailing_slash: bool = False
        self._original_fragment: Optional[str] = None
        self._creator_func: Optional[Callable[..., URLInfo]] = None
        # Mark initialized if raw_url provided (direct instantiation) or set by factory
        self._initialized: bool = raw_url is not None

    # --- Properties --- #

    @property
    def raw_url(self) -> str:
        """Returns the original, unmodified URL string passed to the factory."""
        # Ensure initialized before accessing? No, raw_url is set immediately by factory.
        return self._raw_url

    @functools.cached_property
    def normalized_url(self) -> str:
        """
        Returns the normalized URL string (scheme, netloc, path, params, query),
        excluding the fragment. Returns empty string if invalid.
        """
        if not self._initialized:
            logger.warning(
                "Accessing normalized_url before factory initialization completed."
            )
            # Still return the actual normalized URL if it exists, even if not fully initialized
            # This allows tests to access the property before initialization is complete
        # Return the stored normalized URL (set by factory even if invalid, might be empty or fallback)
        return self._normalized_url if self._normalized_url is not None else ""

    @functools.cached_property
    def parsed(self) -> Optional[ParseResult]:
        """
        Returns the parsed result of the *resolved* URL (before normalization).
        May contain the state just before validation failed, or None if resolution failed.
        """
        if not self._initialized:
            logger.warning("Accessing parsed before factory initialization completed.")
            return None
        return self._parsed  # Set by factory

    @functools.cached_property
    def normalized_parsed(self) -> Optional[ParseResult]:
        """
        Returns the parsed result of the *normalized* URL (scheme, netloc, path, params, query).
        Returns None if the URL is invalid or normalization failed.
        """
        if not self.is_valid:  # Check validity first
            return None
        if not self._initialized:  # Check initialization
            logger.warning(
                "Accessing normalized_parsed before factory initialization completed."
            )
            return None
        return self._normalized_parsed  # Set by factory if valid and normalized

    @functools.cached_property
    def scheme(self) -> Optional[str]:
        """Returns the scheme (e.g., 'http', 'https') from the normalized URL."""
        # Use normalized_parsed if valid, otherwise fallback to parsed for best effort
        p = self.normalized_parsed if self.is_valid else self.parsed
        return p.scheme if p else None

    @functools.cached_property
    def netloc(self) -> Optional[str]:
        """Returns the network location part (e.g., 'www.example.com:8080') from the normalized URL."""
        p = self.normalized_parsed if self.is_valid else self.parsed
        return p.netloc if p else None

    @functools.cached_property
    def path(self) -> Optional[str]:
        """Returns the hierarchical path (e.g., '/path/to/page') from the normalized URL."""
        p = self.normalized_parsed if self.is_valid else self.parsed
        return p.path if p else None

    # @functools.cached_property
    # def path_segments(self) -> Tuple[str, ...]: # Keep commented out for now
    #     """Returns the path split into segments."""
    #     # ... (implementation unchanged)

    # @functools.cached_property
    # def filename(self) -> Optional[str]: # Keep commented out for now
    #     """Extracts the filename from the last path segment."""
    #     # ... (implementation unchanged)

    # @functools.cached_property
    # def extension(self) -> Optional[str]: # Keep commented out for now
    #     """Extracts the file extension from the filename, if present."""
    #     # ... (implementation unchanged)

    @functools.cached_property
    def params(self) -> Optional[str]:
        """Returns parameters for the last path segment (rarely used) from the normalized URL."""
        p = self.normalized_parsed if self.is_valid else self.parsed
        return p.params if p else None

    @functools.cached_property
    def query(self) -> Optional[str]:
        """Returns the query string (e.g., 'a=1&b=two') from the normalized URL."""
        p = self.normalized_parsed if self.is_valid else self.parsed
        return p.query if p else None

    @functools.cached_property
    def fragment(self) -> Optional[str]:
        """
        Returns the original fragment identifier (e.g., 'section'), preserved from the input.
        Returns None if no fragment was present or initialization failed.
        """
        if not self._initialized:
            logger.warning(
                "Accessing fragment before factory initialization completed."
            )
            return None
        return (
            self._original_fragment
        )  # Retrieved by factory, can be None or empty string

    @functools.cached_property
    def hostname(self) -> Optional[str]:
        """
        Returns the hostname (lowercase) from the *parsed* (resolved but pre-normalization) URL.
        Attempts to return even if URL is ultimately invalid.
        """
        p = self.parsed  # Use pre-normalization parsed result
        return p.hostname if p else None

    @functools.cached_property
    def port(self) -> Optional[int]:
        """
        Returns the port number from the *parsed* (resolved but pre-normalization) URL.
        Attempts to return even if URL is ultimately invalid.
        Returns None if port is invalid or unspecified.
        """
        p = self.parsed  # Use pre-normalization parsed result
        try:
            port_val = p.port if p else None
            # Basic validation is done in factory, but double-check range here
            if port_val is not None and not (0 <= port_val <= 65535):
                return None
            return port_val
        except (TypeError, ValueError):
            return None

    @functools.cached_property
    def query_params(self) -> MappingProxyType[str, list[str]]:
        """
        Returns the query string from the *normalized* URL, parsed into an immutable dictionary-like object.
        Keys are parameter names, values are lists of values.
        Returns an empty mapping if invalid or no query.
        """
        q_str = self.query  # Relies on normalized query
        if not q_str:
            return MappingProxyType({})

        try:
            parsed_list = parse_qsl(q_str, keep_blank_values=True, strict_parsing=False)
            params_dict: dict[str, list[str]] = {}
            for key, value in parsed_list:
                params_dict.setdefault(key, []).append(value)
            return MappingProxyType(params_dict)
        except Exception as e:
            logger.warning(f"Failed to parse query string '{q_str}': {e}")
            return MappingProxyType({})

    @functools.cached_property
    def url(self) -> str:
        """
        Returns the reconstructed, normalized URL string, including the original fragment.
        Returns the (potentially non-normalized) fallback URL if invalid.
        """
        if not self._initialized:
            logger.warning("Accessing url before factory initialization completed.")
            # Return the raw input as the best guess if not initialized
            return self._raw_url if self._raw_url is not None else ""

        # Use the normalized URL (without fragment) if valid, otherwise use the stored fallback
        # Ensure _normalized_url is not None before using it
        base_url = (
            self.normalized_url
            if self.is_valid
            else (self._normalized_url if self._normalized_url is not None else "")
        )

        # Append fragment if it existed originally
        frag = self.fragment  # Use fragment property
        if frag is not None and frag:
            # Handle cases where base_url might be empty (e.g., invalid input was just "#frag")
            # Check raw_url as well for this edge case
            if not base_url and self._raw_url and self._raw_url.startswith("#"):
                return f"#{frag}"
            # Ensure base_url is a string before formatting
            return f"{str(base_url)}#{frag}"
        else:
            # Ensure base_url is a string
            return str(base_url)

    # --- Derived Boolean Properties --- #

    @functools.cached_property
    def is_relative(self) -> bool:
        """
        Checks if the URL is relative (lacks scheme and netloc). Based on the *normalized* URL.
        Returns False if the URL is invalid.
        """
        if not self.is_valid:
            return False
        # Check normalized components
        return not self.scheme and not self.netloc

    # @functools.cached_property
    # def has_credentials(self) -> bool: # Keep commented out
    #     """Checks if the URL includes username or password."""
    #     # ... (implementation unchanged)

    @functools.cached_property
    def is_ip_address(self) -> bool:
        """Checks if the hostname (from pre-normalized URL) is an IP address (v4 or v6)."""
        # Use hostname property which uses self.parsed
        hn = self.hostname
        if not hn:  # Check if hostname exists
            return False
        # The validation logic remains the same
        try:
            # Handle IPv6 addresses which may be enclosed in brackets
            if hn.startswith("[") and hn.endswith("]"):
                hn = hn[1:-1]
            ipaddress.ip_address(hn)
            return True
        except ValueError:
            return False

    # @functools.cached_property
    # def is_loopback(self) -> bool: # Keep commented out
    #     """Checks if the hostname is a loopback address."""
    #     # ... (implementation unchanged)

    # @functools.cached_property
    # def is_private(self) -> bool: # Keep commented out
    #     """Checks if the hostname is a private/internal IP address."""
    #     # ... (implementation unchanged)

    # @functools.cached_property
    # def is_multicast(self) -> bool: # Keep commented out
    #     """Checks if the hostname is a multicast IP address."""
    #     # ... (implementation unchanged)

    @functools.cached_property
    def is_absolute(self) -> bool:
        """Checks if the URL is absolute (has scheme or netloc). Based on *normalized* URL."""
        # is_relative checks validity
        return not self.is_relative

    @functools.cached_property
    def is_secure(self) -> bool:
        """Checks if the URL uses a secure scheme (e.g., 'https', 'wss'). Based on *normalized* URL."""
        # Define secure schemes directly here as URLSecurityConfig is no longer imported
        SECURE_SCHEMES = {"https", "wss"}
        # scheme property uses normalized_parsed if valid
        return self.scheme in SECURE_SCHEMES

    # --- Domain Parsing Properties ---

    @functools.cached_property
    def domain_parts(self) -> MappingProxyType[str, Optional[str]]:
        """
        Extracts domain parts from the *hostname* (derived from the pre-normalized URL).
        Uses the `extract_domain_parts` helper function.
        Returns an immutable mapping.
        """
        # Always try to use the hostname from self._parsed if available,
        # as this is the direct result of parsing the resolved URL.
        # self.hostname is a cached_property that also relies on self.parsed.
        hn = None
        if self._parsed:
            hn = self._parsed.hostname

        if not hn:
            logger.debug("domain_parts: No hostname available from self._parsed.")
            # Return empty immutable mapping
            return MappingProxyType(
                {
                    "subdomain": None,
                    "domain": None,
                    "suffix": None,
                    "registered_domain": None,
                }
            )

        try:
            # Call the imported helper function
            parts = extract_domain_parts(hn)
            logger.debug(
                f"domain_parts: extract_domain_parts result for '{hn}': {parts}"
            )
            return MappingProxyType(parts)
        except Exception as e:
            logger.error(
                f"domain_parts: Error calling extract_domain_parts for hostname '{hn}': {e}",
                exc_info=True,
            )
            # Return empty immutable mapping on error
            return MappingProxyType(
                {
                    "subdomain": None,
                    "domain": None,
                    "suffix": None,
                    "registered_domain": None,
                }
            )

    @functools.cached_property
    def subdomain(self) -> Optional[str]:
        """Returns the subdomain part (e.g., 'www'), or None."""
        return self.domain_parts.get("subdomain")

    @functools.cached_property
    def domain(self) -> Optional[str]:
        """Returns the domain part (e.g., 'example'), or None."""
        return self.domain_parts.get("domain")

    @functools.cached_property
    def suffix(self) -> Optional[str]:
        """Returns the public suffix (e.g., 'com', 'co.uk'), or None."""
        return self.domain_parts.get("suffix")

    @functools.cached_property
    def tld(self) -> Optional[str]:
        """Alias for suffix."""
        return self.suffix

    @functools.cached_property
    def registered_domain(self) -> Optional[str]:
        """
        Returns the registered domain (e.g., 'example.com').
        Returns the hostname itself if it's an IP address. Returns None otherwise if not found.
        """
        reg_domain = self.domain_parts.get("registered_domain")
        # Check if it's an IP *after* checking domain_parts result
        # Use the is_ip_address property which handles brackets etc.
        if not reg_domain and self.is_ip_address:
            return self.hostname  # Return IP address string (hostname property)
        return reg_domain

    @functools.cached_property
    def root_domain(self) -> Optional[str]:
        """Alias for registered_domain."""
        return self.registered_domain

    # --- Methods --- #

    # Methods moved from URLInfoManipulationMixin
    def with_scheme(self, scheme: str) -> "URLInfo":
        """Create a new URLInfo instance with a different scheme."""
        if not self.is_valid or not self._normalized_parsed:
            # Consider raising an error or returning a new invalid URLInfo
            from .factory import create_url_info  # Local import

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
                if self.fragment is not None and self.fragment
                else new_url_str_no_frag
            )
            from .factory import create_url_info  # Local import

            return create_url_info(final_url_str, base_url=self.base_url)
        except Exception as e:
            logger.warning(f"Scheme change failed: {e}")  # Use logger
            from .factory import create_url_info  # Local import

            return create_url_info(self.raw_url, self.base_url)  # Fallback

    def with_path(self, path: str) -> "URLInfo":
        """Create a new URLInfo instance with a different path."""
        if not self.is_valid or not self._normalized_parsed:
            from .factory import create_url_info  # Local import

            return create_url_info(self.raw_url, self.base_url)

        try:
            parts = list(self._normalized_parsed)
            parts[2] = path if path.startswith("/") else f"/{path}"  # Replace path
            new_url_str_no_frag = urlunparse(tuple(parts))
            final_url_str = (
                f"{new_url_str_no_frag}#{self.fragment}"
                if self.fragment is not None and self.fragment
                else new_url_str_no_frag
            )
            from .factory import create_url_info  # Local import

            return create_url_info(final_url_str, base_url=self.base_url)
        except Exception as e:
            logger.warning(f"Path change failed: {e}")  # Use logger
            from .factory import create_url_info  # Local import

            return create_url_info(self.raw_url, self.base_url)

    def with_query_params(self, params: dict) -> "URLInfo":
        """Create a new URLInfo instance with updated query parameters."""
        if not self.is_valid or not self._normalized_parsed:
            from .factory import create_url_info  # Local import

            return create_url_info(self.raw_url, self.base_url)

        try:
            from urllib.parse import urlencode  # Import locally if needed

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
                if self.fragment is not None and self.fragment
                else new_url_str_no_frag
            )
            from .factory import create_url_info  # Local import

            return create_url_info(final_url_str, base_url=self.base_url)
        except Exception as e:
            logger.warning(f"Query param update failed: {e}")  # Use logger
            from .factory import create_url_info  # Local import

            return create_url_info(self.raw_url, self.base_url)

    def without_query_params(self, param_names: list) -> "URLInfo":
        """Create a new URLInfo instance with specific query parameters removed."""
        if not self.is_valid or not self._normalized_parsed:
            from .factory import create_url_info  # Local import

            return create_url_info(self.raw_url, self.base_url)

        try:
            from urllib.parse import urlencode  # Import locally if needed

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
                if self.fragment is not None and self.fragment
                else new_url_str_no_frag
            )
            from .factory import create_url_info  # Local import

            return create_url_info(final_url_str, base_url=self.base_url)
        except Exception as e:
            logger.warning(f"Query param removal failed: {e}")  # Use logger
            from .factory import create_url_info  # Local import

            return create_url_info(self.raw_url, self.base_url)

    # Original join method from info.py
    def join(self, relative_url: str) -> "URLInfo":
        """
        Creates a new URLInfo by joining a relative URL with this URL (if valid).
        Uses the factory function for the creation of the new instance.
        """
        if not self.is_valid:
            raise ValueError("Cannot join with an invalid base URL")
        # Use the *normalized* URL (without fragment) as the base
        base = self.normalized_url
        # Import factory locally to avoid circular imports at module level
        from .factory import create_url_info

        return create_url_info(relative_url, base_url=base)

    # Original replace method from info.py
    def replace(self, **kwargs: Any) -> "URLInfo":
        """
        Creates a new URLInfo object with specified components replaced in the *normalized* URL.
        Uses the factory function for the creation of the new instance.
        The original fragment is preserved.
        """
        if not self.is_valid or not self.normalized_parsed:
            # Use normalized_parsed for replacement base
            raise ValueError(
                "Cannot replace components on an invalid or non-normalized URL"
            )

        # Use the normalized parsed result (scheme, netloc, path, params, query)
        new_parsed = self.normalized_parsed._replace(**kwargs)
        new_url_str_no_frag = urlunparse(new_parsed)

        # Add the original fragment back before creating the new instance
        final_url_str = new_url_str_no_frag
        original_frag = self.fragment  # Use property to get original fragment
        if original_frag is not None and original_frag:
            final_url_str = f"{new_url_str_no_frag}#{original_frag}"

        # Re-create using the factory
        from .factory import create_url_info

        # Pass the *original* base_url that this instance was created with.
        # The factory will handle parsing the fragment from final_url_str again.
        return create_url_info(final_url_str, base_url=self.base_url)

    # --- Dunder Methods --- #

    def __str__(self) -> str:
        """Returns the reconstructed, normalized URL string (including fragment)."""
        return self.url  # Use the url property

    def __repr__(self) -> str:
        """Returns a developer-friendly representation."""
        status = "valid" if self.is_valid else f"invalid ({self.error_message})"
        # Use url property for normalized output in repr if valid
        norm_repr = self.url if self.is_valid else self._normalized_url
        # Ensure raw_url and base_url are strings for repr
        raw_repr = self._raw_url if self._raw_url is not None else "None"
        base_repr = self.base_url if self.base_url is not None else "None"

        return (
            f"URLInfo(raw='{raw_repr}', base='{base_repr}', "
            f"normalized='{norm_repr}', status='{status}')"
        )

    def __eq__(self, other: object) -> bool:
        """
        Checks equality based on the fully reconstructed, normalized URL (including fragment)
        for valid URLs, or based on raw_url and base_url for invalid URLs.
        """
        if isinstance(other, URLInfo):
            # Ensure both objects are initialized before comparison
            if not self._initialized or not getattr(other, "_initialized", False):
                return False  # Cannot compare uninitialized objects reliably

            if self.is_valid and other.is_valid:
                # Compare the full .url property (normalized + fragment)
                return self.url == other.url
            elif not self.is_valid and not other.is_valid:
                # Compare inputs for invalid instances
                return (
                    self._raw_url == other._raw_url and self.base_url == other.base_url
                )
            else:
                return False  # One valid, one invalid
        elif isinstance(other, str):
            # Compare full .url property with the string, only if valid and initialized
            return self._initialized and self.is_valid and self.url == other
        return NotImplemented

    def __hash__(self) -> int:
        """
        Computes hash based on the full reconstructed URL (.url) for valid instances,
        or the tuple (raw_url, base_url) for invalid instances. Consistent with __eq__.
        """
        # Ensure initialized before hashing
        if not self._initialized:
            # Hash based on input if not initialized, similar to invalid case
            logger.warning(f"Hashing uninitialized URLInfo(raw='{self._raw_url}')")
            return hash((self._raw_url, self.base_url))

        if self.is_valid:
            return hash(self.url)
        else:
            # Use raw URL and base URL for hashing invalid instances to match __eq__
            return hash((self._raw_url, self.base_url))

    def __bool__(self) -> bool:
        """Returns True if the URL is considered valid by the factory, False otherwise."""
        # Also consider initialization status? No, validity implies initialization.
        return self.is_valid

    def __getstate__(self) -> dict[str, Any]:
        """Prepare the object for pickling. Converts MappingProxyType to dict."""
        state = {}
        for slot in self.__slots__:
            if hasattr(self, slot):
                value = getattr(self, slot)
                # Convert MappingProxyType in slots to dict for pickling
                if isinstance(value, MappingProxyType):
                    state[slot] = dict(value)
                elif slot == "__dict__":
                    # Only include __dict__ if it's not empty and convert internal MappingProxyTypes
                    if value:  # value here is self.__dict__
                        dict_copy = {}
                        for k, v in value.items():
                            if isinstance(v, MappingProxyType):
                                dict_copy[k] = dict(
                                    v
                                )  # Convert MappingProxyType to dict
                            else:
                                dict_copy[k] = v
                        # Only add __dict__ to state if it's not empty after potential conversions
                        if dict_copy:
                            state[slot] = dict_copy
                else:
                    state[slot] = value
        return state

    def __setstate__(self, state: dict[str, Any]) -> None:
        """Restore the object state from pickling."""
        # Restore __dict__ first if present in state
        if "__dict__" in state:
            # Ensure self.__dict__ exists before updating
            if not hasattr(self, "__dict__"):
                super().__setattr__("__dict__", {})  # Initialize __dict__ if missing
            self.__dict__.update(state["__dict__"])
            # No need to delete from state, loop below will skip it

        # Restore slotted attributes using super to bypass our __setattr__
        for slot in self.__slots__:
            if slot in state:
                # Skip __dict__ as it was handled above
                if slot != "__dict__":
                    super().__setattr__(slot, state[slot])
            else:
                # If a slot is missing in the state, initialize it to a default value
                # This handles unpickling older versions that might lack a slot.
                if not hasattr(self, slot):
                    logger.warning(
                        f"__setstate__: Slot '{slot}' missing in state. Initializing to default."
                    )
                    default_value = (
                        None  # Or determine appropriate default based on slot type
                    )
                    if slot == "_initialized":
                        default_value = False
                    elif slot == "is_valid":
                        default_value = False
                    elif slot == "url_type":
                        default_value = URLType.UNKNOWN
                    elif slot == "_raw_url":
                        default_value = ""
                    elif slot == "_original_path_had_trailing_slash":
                        default_value = False
                    # Add other defaults as needed
                    super().__setattr__(slot, default_value)

        # Ensure _initialized is set correctly after restoring state
        # It should be present in the state if saved correctly by __getstate__
        if not hasattr(self, "_initialized"):
            # Fallback: Assume initialized if it was valid, otherwise not.
            # This might be incorrect if an object was pickled mid-factory-creation.
            logger.warning(
                "Restoring URLInfo state: _initialized flag was missing. Inferring from is_valid."
            )
            super().__setattr__("_initialized", getattr(self, "is_valid", False))

    def __setattr__(self, name: str, value: Any) -> None:
        """
        Prevent modification of attributes after initialization by the factory.
        Allows modification only if _initialized is False.
        """
        # Check if '_initialized' exists and is True. Use getattr for safety.
        initialized = getattr(self, "_initialized", False)

        # Allow setting attributes only if not initialized yet.
        # This includes setting __dict__ for cached_property during its first access.
        if not initialized:
            super().__setattr__(name, value)
        # If initialized, only allow internal setting of __dict__ itself (by cached_property)
        elif name == "__dict__":
            super().__setattr__(name, value)
        else:
            # Raise error for any other attribute setting attempt after initialization
            raise AttributeError(
                f"Cannot set attribute '{name}' on immutable URLInfo object after creation by factory"
            )
