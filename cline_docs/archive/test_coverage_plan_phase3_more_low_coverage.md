# Test Coverage Improvement Plan - Phase 3: More Low Coverage Files

Last Updated: 2025-05-21 16:45

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

---

## File: `src/backends/selector.py`
*   **Current Coverage (Reported):** 35% (many lines missed in complex selection logic)
*   **Analysis:** The `BackendSelector` class is responsible for registering, selecting, and initializing backends based on URL patterns and content types. The complex scoring and selection logic has many untested branches.
*   **Proposed Test Cases Sub-tasks:**
    *   **Task: Significantly improve test coverage for `src/backends/selector.py`.**
    *   **Sub-Task 1: Test `BackendCriteria` model.**
        *   **Test 1.1: Initialization with default and custom values.**
        *   **Test 1.2: Field validators (e.g., `priority` range, URL pattern format).**
    *   **Sub-Task 2: Test `BackendSelector.__init__` and initial state.**
        *   **Test 2.1: Default initialization (empty collections).**
        *   **Test 2.2: Lock creation and initialization.**
    *   **Sub-Task 3: Test `BackendSelector.register_backend` thoroughly.**
        *   **Test 3.1: Register class-based backend (production mode).**
        *   **Test 3.2: Register instance-based backend (test mode).**
        *   **Test 3.3: Re-register existing backend (warning log).**
        *   **Test 3.4: Register with custom criteria.**
    *   **Sub-Task 4: Test `BackendSelector._initialize_known_backends`.**
        *   **Test 4.1: First-time initialization.**
        *   **Test 4.2: Already initialized (early return).**
        *   **Test 4.3: Exception during initialization.**
    *   **Sub-Task 5: Test `BackendSelector.select_backend_for_url` - URL and Content Type Matching.**
        *   **Test 5.1: Exact match (URL pattern and content type).**
        *   **Test 5.2: URL match only (content type is None).**
        *   **Test 5.3: URL match with HTML preference when content_type is None.**
        *   **Test 5.4: Fallback to highest priority when no URL match.**
        *   **Test 5.5: No match at all (return None).**
    *   **Sub-Task 6: Test `BackendSelector._evaluate_backend` scoring logic.**
        *   **Test 6.1: Perfect match scoring.**
        *   **Test 6.2: Partial match scoring with various weights.**
        *   **Test 6.3: URL pattern matching with wildcards.**
        *   **Test 6.4: Content type matching (exact, wildcard, no match).**
    *   **Sub-Task 7: Test `BackendSelector.get_backend` - Backend Initialization.**
        *   **Test 7.1: Get existing backend instance.**
        *   **Test 7.2: Create new backend instance.**
        *   **Test 7.3: No matching backend class.**
        *   **Test 7.4: Exception during backend initialization.**
    *   **Sub-Task 8: Test `BackendSelector.close_backend` and `close_all_backends`.**
        *   **Test 8.1: Close specific backend.**
        *   **Test 8.2: Close non-existent backend (no error).**
        *   **Test 8.3: Close all backends.**
        *   **Test 8.4: Exception during backend closing.**

---

## File: `src/processors/quality_checker.py`
*   **Current Coverage (Reported):** 28% (many conditional branches untested)
*   **Analysis:** The `QualityChecker` evaluates processed content against quality criteria. Many conditional branches for different quality checks are untested.
*   **Proposed Test Cases Sub-tasks:**
    *   **Task: Significantly improve test coverage for `src/processors/quality_checker.py`.**
    *   **Sub-Task 1: Test `IssueType` and `IssueLevel` Enums.**
        *   **Test 1.1: Check enum members and values.**
    *   **Sub-Task 2: Test `QualityIssue` model.**
        *   **Test 2.1: Initialization with required and optional fields.**
    *   **Sub-Task 3: Test `QualityConfig` model.**
        *   **Test 3.1: Default initialization.**
        *   **Test 3.2: Custom initialization with all fields.**
    *   **Sub-Task 4: Test `QualityChecker.__init__`.**
        *   **Test 4.1: Initialize with default config (None).**
        *   **Test 4.2: Initialize with custom config.**
    *   **Sub-Task 5: Test `QualityChecker.check_quality` - Content Length Checks.**
        *   **Test 5.1: Content length within limits (no issues).**
        *   **Test 5.2: Content length below minimum (error).**
        *   **Test 5.3: Content length above maximum (warning).**
        *   **Test 5.4: Disabled checks (min_content_length = 0, max_content_length = 0).**
        *   **Test 5.5: Empty or None content.**
    *   **Sub-Task 6: Test `QualityChecker.check_quality` - Heading Checks.**
        *   **Test 6.1: Sufficient headings (no issues).**
        *   **Test 6.2: Too few headings (error).**
        *   **Test 6.3: Heading level exceeds maximum (warning).**
        *   **Test 6.4: Empty headings list.**
    *   **Sub-Task 7: Test `QualityChecker.check_quality` - Internal Link Checks.**
        *   **Test 7.1: Sufficient internal links (no issues).**
        *   **Test 7.2: Too few internal links (warning).**
        *   **Test 7.3: Empty links list.**
    *   **Sub-Task 8: Test `QualityChecker.check_quality` - Metadata Checks.**
        *   **Test 8.1: All required metadata present (no issues).**
        *   **Test 8.2: Missing required metadata (error for each).**
        *   **Test 8.3: Empty metadata.**
        *   **Test 8.4: Custom required_metadata list.**
    *   **Sub-Task 9: Test `QualityChecker.check_quality` - Code Block Checks.**
        *   **Test 9.1: Code blocks within length limits (no issues).**
        *   **Test 9.2: Code blocks too short (warning).**
        *   **Test 9.3: Code blocks too long (warning).**
        *   **Test 9.4: Empty code blocks list.**
    *   **Sub-Task 10: Test `QualityChecker.check_quality` - Metrics Calculation.**
        *   **Test 10.1: Verify all metrics are calculated correctly.**
        *   **Test 10.2: Metrics with empty/None content components.**

---

## File: `src/routes/test_routes.py`
*   **Current Coverage (Reported):** 18% (many routes and WebSocket handlers untested)
*   **Analysis:** This file implements test monitoring routes and WebSocket handlers for real-time test status updates. Most of the WebSocket event handling and route logic is untested.
*   **Proposed Test Cases Sub-tasks:**
    *   **Task: Significantly improve test coverage for `src/routes/test_routes.py`.**
    *   **Sub-Task 1: Test `TestWebSocketManager` class.**
        *   **Test 1.1: Initialization and default state.**
        *   **Test 1.2: `connect` and `disconnect` methods.**
        *   **Test 1.3: `broadcast` method with various message types.**
        *   **Test 1.4: `update_status` method with different status objects.**
        *   **Test 1.5: `add_log` method with different log levels and messages.**
        *   **Test 1.6: `reset_stats` method.**
    *   **Sub-Task 2: Test `init_test_monitoring` function.**
        *   **Test 2.1: Verify pytest hook registration.**
        *   **Test 2.2: Test `pytest_runtest_logreport` hook with passed, failed, and skipped reports.**
    *   **Sub-Task 3: Test WebSocket route handlers.**
        *   **Test 3.1: `/ws/tests` endpoint connection.**
        *   **Test 3.2: WebSocket message handling.**
        *   **Test 3.3: WebSocket disconnection.**
    *   **Sub-Task 4: Test HTTP route handlers.**
        *   **Test 4.1: `/api/tests/run` endpoint with various parameters.**
        *   **Test 4.2: `/api/tests/status` endpoint.**
        *   **Test 4.3: `/api/tests/logs` endpoint.**
        *   **Test 4.4: `/api/tests/reset` endpoint.**
    *   **Sub-Task 5: Test test execution functions.**
        *   **Test 5.1: `_run_tests_in_background` with successful test execution.**
        *   **Test 5.2: `_run_tests_in_background` with test failures.**
        *   **Test 5.3: `_run_tests_in_background` with exceptions during execution.**

---

## File: `src/benchmarking/backend_benchmark.py`
*   **Current Coverage (Reported):** 22% (benchmark execution and reporting logic untested)
*   **Analysis:** This file implements benchmarking functionality for comparing backend performance. The benchmark execution, timing, and reporting logic has low coverage.
*   **Proposed Test Cases Sub-tasks:**
    *   **Task: Significantly improve test coverage for `src/benchmarking/backend_benchmark.py`.**
    *   **Sub-Task 1: Test `BenchmarkConfig` model.**
        *   **Test 1.1: Default initialization.**
        *   **Test 1.2: Custom initialization with all fields.**
        *   **Test 1.3: Field validators and constraints.**
    *   **Sub-Task 2: Test `BenchmarkResult` model.**
        *   **Test 2.1: Initialization with all fields.**
        *   **Test 2.2: Derived metrics calculation.**
        *   **Test 2.3: `to_dict` and serialization methods.**
    *   **Sub-Task 3: Test `BackendBenchmark.__init__` and setup.**
        *   **Test 3.1: Default initialization.**
        *   **Test 3.2: Custom configuration initialization.**
        *   **Test 3.3: Backend registration.**
    *   **Sub-Task 4: Test `BackendBenchmark.run_benchmark` - Single Backend.**
        *   **Test 4.1: Successful benchmark run.**
        *   **Test 4.2: Error during benchmark run.**
        *   **Test 4.3: Timeout handling.**
        *   **Test 4.4: Resource usage tracking.**
    *   **Sub-Task 5: Test `BackendBenchmark.run_comparison` - Multiple Backends.**
        *   **Test 5.1: Successful comparison of multiple backends.**
        *   **Test 5.2: Partial failures (some backends succeed, some fail).**
        *   **Test 5.3: Complete failure (all backends fail).**
    *   **Sub-Task 6: Test `BackendBenchmark.generate_report`.**
        *   **Test 6.1: Report generation with successful results.**
        *   **Test 6.2: Report generation with mixed results.**
        *   **Test 6.3: Different report formats (text, JSON, HTML).**
    *   **Sub-Task 7: Test timing and measurement utilities.**
        *   **Test 7.1: `_measure_time` function.**
        *   **Test 7.2: `_measure_memory` function.**
        *   **Test 7.3: `_measure_cpu` function.**

---

## Implementation Strategy and Best Practices

To efficiently implement these test cases and maximize coverage:

1. **Use Parameterized Tests:** Leverage pytest's parameterization to test multiple scenarios with minimal code duplication.
   ```python
   @pytest.mark.parametrize("url,expected_type", [
       ("https://example.com", URLType.EXTERNAL),
       ("/relative/path", URLType.INTERNAL),
       # More test cases...
   ])
   def test_url_type_determination(url, expected_type):
       # Test implementation
   ```

2. **Mock External Dependencies:** Use `unittest.mock` or `pytest-mock` to isolate the code being tested.
   ```python
   def test_tldextract_usage(mocker):
       mock_extract = mocker.patch("tldextract.extract", return_value=...)
       # Test implementation
   ```

3. **Test Exception Handling:** Explicitly test error paths by forcing exceptions.
   ```python
   def test_exception_handling(mocker):
       mocker.patch("module.function", side_effect=ValueError("Test error"))
       # Test implementation
   ```

4. **Use Fixtures for Common Setup:** Create fixtures for complex objects needed across multiple tests.
   ```python
   @pytest.fixture
   def processed_content():
       return ProcessedContent(...)
   ```

5. **Test Async Code Properly:** Use pytest-asyncio for testing asynchronous functions.
   ```python
   @pytest.mark.asyncio
   async def test_async_function():
       result = await async_function()
       assert result == expected
   ```

6. **Verify Logging:** Test that appropriate log messages are generated.
   ```python
   def test_logging(caplog):
       caplog.set_level(logging.WARNING)
       # Call function that should log
       assert "Expected warning message" in caplog.text
   ```

7. **Test Edge Cases:** Include tests for boundary conditions, empty inputs, and other edge cases.

8. **Measure Coverage Incrementally:** Run coverage reports after implementing each sub-task to track progress.

## Expected Outcomes

After implementing all test cases in this plan:

1. **Coverage Improvement:** Coverage for these files should increase from the current low percentages to at least 90%.

2. **Bug Detection:** The comprehensive testing will likely uncover edge case bugs or inconsistencies.

3. **Documentation:** The tests will serve as executable documentation for the complex logic in these components.

4. **Refactoring Confidence:** Higher test coverage will enable safer refactoring in the future.

5. **Integration Stability:** Better unit test coverage will lead to more stable integration between components.

The implementation should be prioritized based on the criticality of each component to the overall system functionality.