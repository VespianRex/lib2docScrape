# Revised Plan: URL Handling Refactor (Modular Completion)

This plan outlines the steps to complete the refactoring of the URL handling logic into a modular structure based on the existing files in `src/utils/url/` and `tests/url/`.

## Phase 1: Complete Core Implementation & Integration

1.  **Task: Complete `src/utils/url/info.py` (`URLInfo` class):**
    *   **Subtask:** Review the existing (potentially partial) code in `src/utils/url/info.py`.
    *   **Subtask:** Finish the `__init__` method to correctly orchestrate parsing (`urlparse`, `urljoin`), validation (`validate_url` from `.validation`), and normalization (`normalize_url` from `.normalization`). Ensure it handles `base_url`, sets `is_valid`, `error_message`, stores parsed/normalized results, determines `url_type` (from `.types`), and integrates `tldextract`.
    *   **Subtask:** Ensure all properties function correctly with the completed `__init__`.
2.  **Task: Complete `tests/url/test_info.py`:**
    *   **Subtask:** Review the existing (potentially partial) test file.
    *   **Subtask:** Add/complete comprehensive tests covering the `URLInfo` class initialization, properties, tldextract integration, type determination, comparison methods (`__eq__`, `__hash__`), and edge cases.
3.  **Task: Update `src/utils/helpers.py`:**
    *   **Subtask:** Change import to `from src.utils.url import URLInfo, URLType, URLSecurityConfig`.
    *   **Subtask:** Simplify `URLProcessor` if possible (the custom `security_config` might be redundant if `URLInfo` now uses `src.utils.url.security` directly).
    *   **Subtask:** Remove the `is_safe` check in `sanitize_and_join_url`.
4.  **Task: Update Integration Tests:**
    *   **Subtask:** Modify `tests/test_url_handling_integration.py` import to `from src.utils.url import URLInfo, URLType`.

## Phase 2: Test Alignment & Cleanup (TDD Approach)

5.  **Task: Align All Modular Tests (`tests/url/`):**
    *   **Subtask (Red/Green/Refactor):** Review tests in `tests/url/` (`test_types.py`, `test_security.py`, `test_validation.py`, `test_normalization.py`, `test_info.py`). Ensure they comprehensively cover the modular functions and the integrated `URLInfo` behavior.
6.  **Task: Cleanup Conflicting Files:**
    *   **Subtask:** Delete the monolithic `src/utils/url_info.py` file.
    *   **Subtask:** Delete the `tests/test_url_handling_tldextract.py` file.

## Phase 3: Documentation & Finalization

7.  **Task: Update Documentation:**
    *   **Subtask:** Update `docs/url_handling.md`, `docs/url_handling_migration.md` to describe the modular structure and usage. Remove mentions of caching.
    *   **Subtask:** Update/remove `tdd/url_enhancements.md`.
    *   **Subtask:** Update `tdd.md` log.
    *   **Subtask:** Update/delete `url_refactor_plan.md`.
8.  **Task: Run Full Test Suite:**
    *   **Subtask:** Execute all tests.
    *   **Subtask:** Address any failures.

## Diagram (Mermaid)

```mermaid
graph TD
    subgraph Phase 1: Complete Core Implementation & Integration
        A[Complete src/utils/url/info.py (URLInfo.__init__, methods)] --> B[Integrate validation & normalization functions];
        B --> C[Ensure tldextract integration];
        C --> D[Complete tests/url/test_info.py];
        D --> E[Update src/utils/helpers.py (import, adapter)];
        E --> F[Update tests/test_url_handling_integration.py (import)];
    end

    subgraph Phase 2: Test Alignment & Cleanup
        G[Review/Enhance tests in tests/url/] --> H[Ensure coverage for modular functions & URLInfo];
        H --> I[Delete src/utils/url_info.py];
        I --> J[Delete tests/test_url_handling_tldextract.py];
    end

    subgraph Phase 3: Documentation & Finalization
        K[Update url_handling*.md Docs for modular structure] --> L[Update/Remove tdd/url_enhancements.md];
        L --> M[Update tdd.md Log];
        M --> N[Update/Delete url_refactor_plan.md];
        N --> O[Run Full Test Suite];
        O --> P{Address Test Failures};
        P -- Loop --> O;
        P -- Done --> Q[Refactor Complete (Modular)];
    end

    F --> G;
    J --> K;