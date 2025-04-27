# Current Task: Fix Test Failures (Phase 1)

## Objective
Address the test failures outlined in `docs/TestSolvingPlan.md`, starting with Phase 1: URL Utilities (`src/utils/url/`).

## Current Step
**Phase 1: URL Utilities (`src/utils/url/`)**
*   **Task 1.1 (`info.py`): Fix `URLInfo` Initialization & Validation**
    *   ✅ Subtask 1.1.1: Implement port validation fix (Issue E, Test `test_invalid_url_initialization[http://example.com:99999-Invalid port]`). Catch `ValueError`, set correct error, prevent `UnboundLocalError`.
    *   ✅ Subtask 1.1.2: Implement scheme validation (Issue B, Tests `test_valid_url_initialization[file:///...]`, `test_invalid_url_initialization[ftp://...]`). Allow `file`, disallow `ftp` with auth.
    *   ✅ Subtask 1.1.3: Implement security pattern checks (Issue C, J, Tests `test_invalid_url_initialization[...]` for traversal, XSS, private IP, null byte; `test_validate_security_patterns`). Ensure correct error messages.
    *   ✅ Subtask 1.1.4: Implement invalid label check (Issue D, Test `test_invalid_url_initialization[http://<invalid>...]`). Ensure `normalize_hostname` raises `ValueError`.
    *   ✅ Subtask 1.1.5: Fix "Missing host" vs "Missing netloc" (Issue G, Test `test_validate_netloc`).
*   **Task 1.2 (`info.py`): Fix `URLInfo` Normalization**
    *   ✅ Subtask 1.2.1: Implement trailing slash logic (Issue A, Tests `test_valid_url_initialization[http://example.com]`, `test_valid_url_initialization[http://localhost:8080]`).
    *   ✅ Subtask 1.2.2: Implement path normalization using `posixpath.normpath` (Issue I, Test `test_valid_url_initialization[http://EXAMPLE.com:80/./path/../other/]`).
*   **Task 1.3 (`info.py`): Fix `URLInfo` Properties**
    *   ✅ Subtask 1.3.1: Fix `netloc` property to strip auth (Issue C, Test `test_url_properties`).
    *   ✅ Subtask 1.3.2: Implement `tldextract` fallbacks for IP/localhost (Issue H, Tests `test_tldextract_properties[...]`).
*   **Task 1.4 (`normalization.py`): Fix Normalization Functions**
    *   ✅ Subtask 1.4.1: Fix `normalize_hostname` to raise `ValueError` correctly (Test `test_normalize_hostname`).
    *   ➡️ **Subtask 1.4.2:** Fix `normalize_path` for empty input (Test `test_normalize_path`).
*   Task 1.5 (`validation.py`): Fix Validation Functions & Tests

## Next Steps
1.  Read `src/utils/url/normalization.py`.
2.  Implement the fix for Subtask 1.4.2 (Fix `normalize_path` for empty input).
3.  Update `docs/TestSolvingPlan.md` to mark Subtask 1.4.2 as complete.
4.  Update this file (`currentTask.md`) for the next subtask.
5.  Run relevant tests to confirm the fixes.