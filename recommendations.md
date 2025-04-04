# Code Improvement Recommendations

This list outlines prioritized recommendations based on the codebase analysis performed on [Date - Placeholder, will update later].

- [x] **1. (Critical) Fix URL Handling in Backend Selector:** Refactor `src/backends/selector.py` to use the correct `URLInfo` class from `src/utils/url_info.py` instead of the deprecated `URLProcessor`. Update imports.
- [x] **2. (High/Security) Implement Robust HTML Sanitization (`bleach`):** Replace custom sanitization in `src/processors/content_processor.py` with the `bleach` library. (Completed during test fixing)
- [ ] **3. (High/Maintainability) Use `markdownify` Library:** Refactor `src/processors/content_processor.py` to use the `markdownify` library for HTML-to-Markdown conversion instead of the custom `_format_structure_to_markdown`.
- [x] **4. (High/Redundancy) Remove Redundant Code:**
    - [x] Delete `src/backends/http.py`.
    - [x] Delete `src/models/url.py`.
    *   [x] Remove the `URLInfo` dataclass and `normalize_url`/`is_valid_url` functions from `src/base.py`.
    *   [x] Remove the corresponding import from `src/__init__.py`.
- [ ] **5. (High/Functionality) Implement Recursive Crawling:** Refactor `src/crawler.py` to implement proper recursive link following based on `depth`, using `_should_crawl_url` (refactored to use `URLInfo`) and managing the crawl queue/tasks.
- [ ] **6. (High/Modularity) Refactor Large Files:**
    *   Move `ProjectIdentifier` from `src/crawler.py` to `src/utils/project_identifier.py`.
    *   Move `DuckDuckGoSearch` from `src/crawler.py` to `src/utils/search.py` (or similar).
    *   Break down long methods within `DocumentationCrawler`.
- [ ] **7. (Medium) Refactor `_should_crawl_url`:** Update `src/crawler.py`'s `_should_crawl_url` to leverage validation from `src/utils/url_info.py`.
- [ ] **8. (Medium) Improve Test Coverage:** Generate a coverage report (`uv run pytest --cov=src`) and add tests for uncovered areas, particularly critical logic.
- [ ] **9. (Medium) Address Test Compatibility Workaround (`content_processor.py`):** Investigate why `content_processor.py` filters structure output for tests. Align tests and processor output.
- [ ] **10. (Medium) Simplify Backend Scoring (`selector.py`):** Refactor and document the scoring logic in `src/backends/selector.py::_evaluate_backend`. Consider making weights configurable.
- [ ] **11. (Medium) Externalize `ProjectIdentifier` Patterns:** Move hardcoded regex/keyword patterns from `src/crawler.py` (within `ProjectIdentifier`) to a configuration file or constants module.
- [ ] **12. (Medium) Make `URLInfo` Configurable:** Consider making validation constants in `src/utils/url_info.py` configurable.
- [ ] **13. (Medium) Consider CI Pipeline:** Set up automated testing/linting via CI if not already present.
- [ ] **14. (Low) Remove Debug Code:** Remove all `print` statements (active and commented) from the codebase. Use logging instead.
- [ ] **15. (Low) Refine Error Handling:** Use more specific exception handling where appropriate instead of broad `except Exception`.
- [ ] **16. (Low) Evaluate `lxml` (Performance):** Consider `lxml` parser for `BeautifulSoup` if HTML parsing performance is a bottleneck.
- [ ] **17. (User Request) Integrate Scrapy as an additional backend:** Add Scrapy as a new backend option, register it with the `BackendSelector`, and provide criteria for its selection (e.g., for complex sites or deep crawls).