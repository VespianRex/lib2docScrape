# Test Coverage Improvement Plan - Phase 3: More Low Coverage Files

Last Updated: 2025-05-21 15:35

This plan targets additional files identified with low test coverage. The goal is to bring them as close to 100% as feasible.

---

## File: `src/utils/url_info_tldextract.py`
*   **Current Coverage (Reported):** 14% (6 lines missed out of 7, but file is 718 lines long)
*   **Analysis:** Implements a comprehensive `URLInfo` class for URL parsing, validation, normalization, and type determination using `tldextract`. The reported coverage is not representative. Extensive testing is needed for its many methods and properties.
*   **Proposed Test Cases Sub-tasks:**
    *   **Task: Significantly improve test coverage for `src/utils/url_info_tldextract.py`.**
    *   **Sub-Task 1: Test `URLType` Enum.**
        *   **Test 1.1: Check enum members and values.**
    *   **Sub-Task 2: Test `URLSecurityConfig` (Constants).**
        *   **Test 2.1: Verify some key constants.**
    *   **Sub-Task 3: Test `URLInfo.__init__` - Basic Initialization and Invalid URL states.**
        *   **Test 3.1: `url` is `None` or empty string.**
        *   **Test 3.2: `url` is not a string.**
        *   **Test 3.3: General exception during `__init__` (e.g., mock `_parse_and_resolve` to raise error).**
        *   **Test 3.4: `_parse_and_resolve` sets `error_message` but `_parsed` remains `None`.**
    *   **Sub-Task 4: Test `URLInfo._parse_and_resolve` thoroughly.**
        *   **Test 4.1: `raw_url` is not a string or empty.**
        *   **Test 4.2: Disallowed schemes (`javascript:`, `data:`).**
        *   **Test 4.3: Protocol-relative URLs (with/without `base_url`).**
        *   **Test 4.4: Adding default scheme (`http`) if missing (and when not to add it).**
        *   **Test 4.5: URL resolution with `base_url` (relative, absolute, full URLs, base_url without scheme, base_url path handling).**
        *   **Test 4.6: `urljoin` `ValueError` during resolution.**
        *   **Test 4.7: Fragment removal and auth removal from netloc.**
        *   **Test 4.8: `tldextract` usage (called for domains, not for IPs/localhost).**
        *   **Test 4.9: `urlparse` `ValueError` (final parsing).**
    *   **Sub-Task 5: Test `URLInfo._validate` and its helper methods (`_validate_scheme`, `_validate_netloc`, `_validate_port`, `_validate_path`, `_validate_query`, `_validate_security_patterns`).**
        *   For each helper, test various valid and invalid inputs covering all branches (e.g., private IPs, loopback IPs, invalid domains, path traversal, XSS patterns, etc.).
    *   **Sub-Task 6: Test `URLInfo._normalize_path`.**
        *   Test various path structures: empty, `.` and `..` resolution, relative vs. absolute, trailing slash preservation, special character quoting, unquoting/encoding failures.
    *   **Sub-Task 7: Test `URLInfo._normalize` (orchestration and specific normalization logic).**
        *   Test early exit conditions.
        *   Hostname normalization (lowercase, IDNA).
        *   `tldextract` result usage and fallbacks.
        *   Port removal for default schemes.
        *   Query parameter normalization (order, encoding).
        *   Exception handling during normalization.
    *   **Sub-Task 8: Test `URLInfo._determine_url_type` (static method).**
        *   Test `UNKNOWN`, `INTERNAL`, `EXTERNAL` cases based on `normalized_url` and `base_url` comparisons (considering registered domains).
    *   **Sub-Task 9: Test all Properties (e.g., `scheme`, `netloc`, `path`, `domain`, `normalized_url`, etc.).**
        *   Test for correct value extraction from `_parsed` or `_normalized_parsed`.
        *   Test behavior when underlying parsed objects are `None`.
        *   Test properties relying on `_tld_extract_result` with IPs/localhost.
        *   Verify `functools.cached_property` behavior (getter called once).
    *   **Sub-Task 10: Test `__eq__`, `__hash__`, `__str__`, `__repr__`.**
    *   **Sub-Task 11: Test `__setattr__` (immutability after `_initialized`).**