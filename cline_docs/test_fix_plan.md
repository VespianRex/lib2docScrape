# Test Fix Plan

This plan outlines the steps to address the test failures identified in the project.

**Phase 1: Address `ScrapyBackend.crawl()` `TypeError`**
1.  **Goal:** Resolve the `TypeError: ScrapyBackend.crawl() missing 1 required positional argument: 'config'` in `tests/test_scrapy_backend.py`.
2.  **Steps:**
    *   Examine the `ScrapyBackend.crawl()` method signature in `src/backends/scrapy_backend.py`.
    *   Review how `ScrapyBackend.crawl()` is invoked in the failing tests: `test_crawl_with_error` and `test_rate_limiting` within `tests/test_scrapy_backend.py`.
    *   Modify the test calls to correctly pass the `config` argument.

**Phase 2: Investigate `aiohttp` Mocking in `test_url_handling_integration.py`**
1.  **Goal:** Fix the `AssertionError: Expected 'get' to have been called once. Called 0 times.` in `tests/test_url_handling_integration.py`.
2.  **Steps:**
    *   Analyze the `aiohttp.ClientSession` mocking setup in `tests/test_url_handling_integration.py`.
    *   Understand how `src/crawler.py` utilizes the `HTTPBackend` and, by extension, `aiohttp.ClientSession`.
    *   Review the usage of `aiohttp.ClientSession` within `src/backends/http_backend.py`.
    *   Propose and implement corrections to the mocking logic or the crawler's interaction with the HTTP backend.

**Phase 3: Resolve `BackendSelector` Issues**
1.  **Goal:** Address `ValueError: Backend class '...' not registered.` errors appearing in `tests/test_base.py`, `tests/test_crawl4ai.py`, and `tests/test_crawler_advanced.py`.
2.  **Steps:**
    *   Study the backend registration and selection mechanisms in `src/backends/selector.py`.
    *   Examine how `BackendSelector` is initialized and used in `src/crawler.py`.
    *   Investigate the failing tests to determine why backends are not being correctly identified for the provided URLs. This may involve checking URL normalization, criteria matching for backends, or the registration process itself.

**Phase 4: Address `BackendCriteria` Validation Errors**
1.  **Goal:** Fix `pydantic_core._pydantic_core.ValidationError: 1 validation error for BackendCriteria` in `tests/test_crawler.py`.
2.  **Steps:**
    *   Locate and review the definition of the `BackendCriteria` model (likely in `src/backends/base.py` or a dedicated models file).
    *   Examine how `BackendCriteria` objects are instantiated in the failing tests within `tests/test_crawler.py`.
    *   Adjust the instantiation to comply with Pydantic's validation rules.

**Phase 5: Fix `QualityChecker` Mock**
1.  **Goal:** Resolve `AttributeError: Mock object has no attribute 'check'` in `tests/test_quality.py`.
2.  **Steps:**
    *   Review how the `QualityChecker` is mocked in `tests/test_quality.py`.
    *   Ensure the mock object correctly implements or is attributed with the `check` method.

**Phase 6: Systematically Address Remaining Failures**
1.  **Goal:** Resolve all other outstanding test failures.
2.  **Steps:** This will be an iterative process. For each remaining failure:
    *   Carefully analyze the error message and traceback.
    *   Read the relevant source and test files.
    *   Develop and implement a targeted fix.

**Phase 7: Update Documentation**
1.  **Goal:** Ensure all project documentation accurately reflects the implemented fixes and current project state.
2.  **Steps:**
    *   Update `cline_docs/projectRoadmap.md`.
    *   Update `cline_docs/currentTask.md` (this will likely involve creating a new task for the test fixing effort).
    *   Update `cline_docs/codebaseSummary.md` with a summary of the fixes.
    *   Create or update `cline_docs/historical_test_fix_log.md` to document the fixes.

**Phase 8: Final Review and Mode Switch**
1.  **Goal:** Confirm all tests are passing and documentation is current.
2.  **Steps:**
    *   Execute the full test suite.
    *   Verify the accuracy of all updated documentation.
    *   Request a switch to "orchestrator" mode to proceed with further project tasks.