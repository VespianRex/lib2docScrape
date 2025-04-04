# Current Task: Implement Recommendation #2

## Objective
Replace custom sanitization logic in `src/processors/content_processor.py` with the `bleach` library for improved security against XSS and other injection attacks.

## Plan
1.  **Add Dependency:** Add `bleach` to the project dependencies in `pyproject.toml`. Execute `uv sync` to install it.
2.  **Read Files:**
    *   Read `src/processors/content_processor.py`.
    *   Read `src/processors/content/models.py` (to check `ProcessorConfig`).
3.  **Modify `content_processor.py`:**
    *   Import `bleach`.
    *   Define allowed HTML tags and attributes (potentially using `bleach.sanitizer.ALLOWED_TAGS` and `ALLOWED_ATTRIBUTES` as a base, adding necessary ones like `pre`, `code`, table tags, `img[src]`, `a[href]`, etc.). Store these in constants or potentially make them configurable via `ProcessorConfig`.
    *   Replace the `_sanitize_soup` method implementation with a call to `bleach.clean()`. Pass the string representation of the relevant HTML part (e.g., `str(soup)`) to `bleach.clean()`, along with the defined allowed tags and attributes. Re-parse the cleaned HTML string back into a `BeautifulSoup` object if necessary for subsequent processing steps.
    *   Remove the `_sanitize_soup` call from the `process` method (around line 137) and integrate the `bleach.clean()` call appropriately within the `process` method's flow (likely after initial parsing and unescaping, before structure/metadata extraction).
    *   Remove the `blocked_attributes` field from `ProcessorConfig` in `src/processors/content/models.py` as `bleach` handles allowed attributes directly. Update the `ContentProcessor.__init__` and `configure` methods accordingly.
4.  **Apply Changes:** Use `apply_diff` to modify the files.
5.  **Run Tests:** Execute `uv run pytest tests/test_content_processor.py tests/test_content_processor_edge.py` to verify the sanitization changes. Analyze and fix any failures.
6.  **Run Full Test Suite:** Execute `uv run pytest` to check for broader regressions.
7.  **Update Documentation:** Update `codebaseSummary.md` and `techStack.md` to reflect the use of `bleach`.