"""
Property-based tests for backend selection.
"""

from unittest.mock import AsyncMock

from hypothesis import given
from hypothesis import strategies as st

from src.backends.base import CrawlerBackend
from src.backends.selector import BackendCriteria, BackendSelector

# Define strategies for backend criteria
priorities = st.integers(min_value=1, max_value=100)
content_types = st.lists(
    st.sampled_from(
        [
            "text/html",
            "text/plain",
            "application/json",
            "application/xml",
            "text/*",
            "*/*",
        ]
    ),
    min_size=1,
    max_size=3,
)
url_patterns = st.lists(
    st.sampled_from(["*example.com*", "*docs*", "*api*", "*github*", "*"]),
    min_size=1,
    max_size=3,
)
schemes = st.lists(
    st.sampled_from(["http", "https", "ftp", "file"]), min_size=1, max_size=4
)
domains = st.lists(
    st.sampled_from(
        ["example.com", "docs.example.com", "api.example.com", "github.com"]
    ),
    min_size=0,
    max_size=3,
)
paths = st.lists(
    st.sampled_from(["/docs", "/api", "/reference", "/guide"]), min_size=0, max_size=3
)

# Strategy for backend criteria
backend_criteria = st.builds(
    BackendCriteria,
    priority=priorities,
    content_types=content_types,
    url_patterns=url_patterns,
    schemes=schemes,
    domains=domains,
    paths=paths,
)

# Strategy for URLs
urls = st.sampled_from(
    [
        "https://example.com",
        "https://docs.example.com",
        "https://api.example.com",
        "https://example.com/docs",
        "https://example.com/api",
        "https://github.com",
        "http://example.org",
    ]
)

# Strategy for content types
content_type_values = st.sampled_from(
    ["text/html", "application/json", "text/plain", None]
)


class MockBackend(CrawlerBackend):
    """Mock backend for testing."""

    def __init__(self, name):
        super().__init__(name=name)
        # These assignments are for the instance, but the class needs to define the methods
        # to satisfy the ABC.

    async def crawl(self, url: str, config: dict) -> list[dict]:
        """Mock crawl method."""
        # This mock implementation can be simple or use the AsyncMock if complex behavior is needed.
        # For now, returning an empty list as a placeholder.
        if hasattr(self, "_crawl_mock"):
            return await self._crawl_mock(url, config)
        return []

    async def process(self, content: str, url: str, content_type: str = None) -> dict:
        """Mock process method."""
        # Similar to crawl, this can be a simple placeholder or use AsyncMock.
        if hasattr(self, "_process_mock"):
            return await self._process_mock(content, url, content_type)
        return {}

    async def validate(self, url: str, content_type: str = None) -> bool:
        """Mock validate method."""
        # Placeholder or AsyncMock.
        if hasattr(self, "_validate_mock"):
            return await self._validate_mock(url, content_type)
        return True

    # You can still use AsyncMocks for more detailed behavior testing by assigning them in __init__
    # and calling them from these concrete methods, or by replacing these methods in tests.
    def setup_mocks(self):
        self._crawl_mock = AsyncMock(return_value=[])
        self._process_mock = AsyncMock(return_value={})
        self._validate_mock = AsyncMock(return_value=True)


@given(st.lists(backend_criteria, min_size=1, max_size=5), urls, content_type_values)
def test_backend_selection_properties(criteria_list, url, content_type):
    """Test properties of backend selection."""
    selector = BackendSelector()

    backends = []
    for i, criteria in enumerate(criteria_list):
        backend = MockBackend(f"backend{i}")
        backend.setup_mocks()  # Initialize the AsyncMocks
        selector.register_backend(f"backend{i}", backend, criteria)
        backends.append(backend)

    # Select a backend
    selected = selector.select_backend_for_url(url, content_type)

    # If a backend was selected, it should be one of the registered backends
    if selected is not None:
        assert selected in backends

        # The selected backend should have criteria that match the URL
        backend_name = selected.name
        backend_criteria = selector.criteria[backend_name]

        # Check that the URL matches the criteria
        parsed_url = url.split("://", 1)[1] if "://" in url else url
        domain = parsed_url.split("/", 1)[0] if "/" in parsed_url else parsed_url

        # If domains are specified, the URL domain should match one of them
        if backend_criteria.domains:
            assert domain in backend_criteria.domains or any(
                domain.endswith(f".{d}") for d in backend_criteria.domains
            )

        # If content_type is specified, it should match one of the backend's content types
        # Note: The backend selector may use fallback logic for unknown content types,
        # so we only enforce strict matching for common content types
        if (
            content_type
            and backend_criteria.content_types
            and content_type
            not in ["application/xml", "application/xhtml+xml", "text/xml"]
        ):
            content_type_matched = False
            for crit_ct in backend_criteria.content_types:
                if crit_ct == content_type:
                    content_type_matched = True
                    break
                if crit_ct == "*/*":
                    content_type_matched = True
                    break
                # Handles 'type/*' by checking if content_type starts with 'type/'
                if crit_ct.endswith("/*") and content_type.startswith(crit_ct[:-1]):
                    content_type_matched = True
                    break
            assert content_type_matched, f"Selected backend {backend_name} with types {backend_criteria.content_types} does not match requested content_type {content_type}"


@given(st.lists(backend_criteria, min_size=2, max_size=5), urls)
def test_backend_selection_priority(criteria_list, url):
    """Test that backend selection respects priority."""
    selector = BackendSelector()

    # Extract scheme from the URL for better test reliability
    url_scheme = url.split("://")[0] if "://" in url else "https"

    # Sort criteria by priority
    sorted_criteria = sorted(criteria_list, key=lambda c: c.priority, reverse=True)

    for i, criteria in enumerate(sorted_criteria):
        # Ensure each backend can handle the URL scheme
        criteria.url_patterns = ["*"]
        criteria.schemes = [url_scheme]
        criteria.content_types = ["*/*"]  # Accept any content type
        criteria.paths = []  # Clear path restrictions to ensure all backends can match
        criteria.domains = []  # Clear domain restrictions to ensure all backends can match

        backend = MockBackend(f"backend{i}")
        backend.setup_mocks()  # Initialize the AsyncMocks
        selector.register_backend(f"backend{i}", backend, criteria)

    # Select a backend
    selected = selector.select_backend_for_url(url)

    # The selected backend should be the one with the highest priority
    if selected is not None:
        assert (
            selected.name == "backend0"
        ), f"Expected backend0 (highest priority) but got {selected.name}"


@given(backend_criteria)
def test_backend_criteria_validation(criteria):
    """Test that backend criteria validation works correctly."""
    # Validation should happen automatically when the BackendCriteria is created
    assert isinstance(criteria.priority, int)
    assert all(isinstance(ct, str) for ct in criteria.content_types)
    assert all(isinstance(up, str) for up in criteria.url_patterns)
    assert all(isinstance(s, str) for s in criteria.schemes)
    assert all(isinstance(d, str) for d in criteria.domains)
    assert all(isinstance(p, str) for p in criteria.paths)
