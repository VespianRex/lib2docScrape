# Test Coverage Improvement Plan - Phase 2: Low (but >0%) Coverage Files

Last Updated: 2025-05-21 15:32

This plan targets files identified with low, but non-zero, test coverage. The goal is to bring them as close to 100% as feasible.

---

## File: `src/crawler/crawler.py` (Sequential Crawler)
*   **Current Coverage (Reported):** 96% (28 lines missed)
*   **Analysis:** This is the existing sequential crawler. The `crawl` method is a placeholder. Missed lines are likely in `__init__` branches or specific logging paths.
*   **Proposed Test Cases Sub-tasks:**
    *   **Task: Achieve 100% coverage for `src/crawler/crawler.py`.**
    *   **Sub-Task 1: Test `Crawler.__init__` branches.**
        *   **Details & Test Logic:**
            *   **Test 1.1: `rate_limit == 0` or negative.**
                ```pseudocode
                config_zero = CrawlConfig(rate_limit=0)
                crawler_zero = Crawler(config=config_zero)
                ASSERT crawler_zero.rate_limiter.requests_per_second == float('inf')
                
                // Assuming Pydantic model for CrawlConfig validates rate_limit >= 0.
                // If negative values are possible and lead to rate_limit <=0, test that too.
                // config_neg = CrawlConfig(rate_limit=-1) 
                // crawler_neg = Crawler(config=config_neg)
                // ASSERT crawler_neg.rate_limiter.requests_per_second == float('inf')
                ```
            *   **Test 1.2: Defaulting of `config` argument.**
                ```pseudocode
                crawler_default_config = Crawler(config=None) // Explicitly pass None
                ASSERT isinstance(crawler_default_config.config, CrawlConfig) // Check it defaulted
                // Check that the default CrawlConfig().rate_limit is used for RateLimiter
                default_cfg_for_rate_check = CrawlConfig()
                expected_rps = 1.0 / default_cfg_for_rate_check.rate_limit if default_cfg_for_rate_check.rate_limit > 0 else float('inf')
                ASSERT crawler_default_config.rate_limiter.requests_per_second == expected_rps
                ```

    *   **Sub-Task 2: Test `Crawler.crawl` method thoroughly.**
        *   **Details & Test Logic:**
            *   **Test 2.1: Call with varied `CrawlTarget` parameters to ensure all are passed through.**
                ```pseudocode
                crawler = Crawler()
                result = await crawler.crawl(
                    target_url="http://example.com/test-crawl",
                    depth=3,
                    follow_external=True,
                    content_types=["application/json", "text/xml"],
                    exclude_patterns=["/api/", "/v1/"],
                    include_patterns=["/data/", "/archive/"], // Note: param name in CrawlTarget
                    max_pages=50,
                    allowed_paths=["/data/items/", "/archive/specific/"],
                    excluded_paths=["/data/raw/", "/archive/temp/"]
                )
                ASSERT result.target.url == "http://example.com/test-crawl"
                ASSERT result.target.depth == 3
                ASSERT result.target.follow_external is True
                ASSERT result.target.content_types == ["application/json", "text/xml"]
                ASSERT result.target.exclude_patterns == ["/api/", "/v1/"]
                ASSERT result.target.include_patterns == ["/data/", "/archive/"]
                ASSERT result.target.max_pages == 50
                ASSERT result.target.allowed_paths == ["/data/items/", "/archive/specific/"]
                ASSERT result.target.excluded_paths == ["/data/raw/", "/archive/temp/"]
                
                ASSERT result.stats.pages_crawled == 1 // Placeholder behavior
                ASSERT len(result.documents) == 1      // Placeholder behavior
                ```
            *   **Test 2.2: Ensure logger call is covered.**
                ```pseudocode
                // In test using caplog fixture (pytest)
                crawler = Crawler()
                await crawler.crawl(target_url="http://logtest.com", depth=1, follow_external=False, content_types=[], exclude_patterns=[], include_patterns=[], max_pages=1, allowed_paths=[], excluded_paths=[])
                ASSERT "Crawling http://logtest.com with depth=1" in caplog.text
                ```

    *   **Sub-Task 3: Review `CrawlerOptions` (lines 14-452).**
        *   **Details & Test Logic:**
            *   **Test 3.1: Basic instantiation with default and custom values.**
                ```pseudocode
                options_default = CrawlerOptions()
                ASSERT options_default.verify_ssl is True 
                ASSERT options_default.javascript_rendering is False

                options_custom = CrawlerOptions(verify_ssl=False, javascript_rendering=True, extract_images=False)
                ASSERT options_custom.verify_ssl is False
                ASSERT options_custom.javascript_rendering is True
                ASSERT options_custom.extract_images is False
                ```
            *   *If specific fields in `CrawlerOptions` have validators or complex defaults not covered by simple instantiation, those would need dedicated tests. However, it appears to be a straightforward model.*

---

## File: `src/utils/error_handler.py`
*   **Current Coverage (Reported):** 6% (15 lines missed out of 16, but file is much larger)
*   **Analysis:** A comprehensive error handling system. Missed lines are likely due to untested enum members, specific error categorization paths, logging levels, and callback mechanisms.
*   **Proposed Test Cases Sub-tasks:**
    *   **Task: Achieve 100% coverage for `src/utils/error_handler.py`.**
    *   **Sub-Task 1: Test `ErrorContext` class.**
        *   **Test 1.1: Instantiation with all args and default `details`.**
        *   **Test 1.2: `to_dict()` method.**
    *   **Sub-Task 2: Test `ErrorHandler.__init__` and initial state.**
    *   **Sub-Task 3: Test `ErrorHandler.register_callback` and `_call_callbacks`.**
        *   **Test 3.1: Register and trigger a callback (check args, backward compatible "message").**
        *   **Test 3.2: Register multiple callbacks for one category.**
        *   **Test 3.3: Callback raises an exception (ensure logging and continuation).**
        *   **Test 3.4: `_call_callbacks` with `error_details` already containing "message".**
    *   **Sub-Task 4: Test `ErrorHandler._categorize_error` for all categories.**
        *   Provide a list of (ExceptionInstance, ExpectedCategory) and assert.
    *   **Sub-Task 5: Test `ErrorHandler._log_error` for all `ErrorLevel`s.**
        *   Use `caplog` or mock `src.utils.error_handler.logger` to verify correct log method and content.
    *   **Sub-Task 6: Test `ErrorHandler.handle_error` comprehensively.**
        *   **Test 6.1: Category explicitly provided (ensure `_categorize_error` is not called).**
        *   **Test 6.2: Category auto-detected.**
    *   **Sub-Task 7: Test `ErrorHandler.get_error_counts` and `reset_error_counts`.**
    *   **Sub-Task 8: Test global convenience functions (`handle_error`, `register_error_callback`, etc.) by patching the global `error_handler` instance's methods.**

---

## File: `src/processors/content_processor.py`
*   **Current Coverage (Reported):** 10% (9 lines missed out of 10, but file is much larger)
*   **Analysis:** Complex content processing pipeline. Low coverage implies many paths in format detection, HTML cleaning, data extraction, and error handling are untested.
*   **Proposed Test Cases Sub-tasks:**
    *   **Task: Significantly improve test coverage for `src/processors/content_processor.py`.**
    *   **Sub-Task 1: Test `DefaultProcessorConfig` instantiation.** (Covers lines 14-22)
    *   **Sub-Task 2: Test `ContentProcessor.__init__` scenarios.**
        *   **Test 2.1: `config=None`, `ProcessorConfig` available.**
        *   **Test 2.2: `config=None`, `ProcessorConfig` unavailable (fallback to `DefaultProcessorConfig`).**
        *   **Test 2.3: `config` provided (custom config object).**
    *   **Sub-Task 3: Test `ContentProcessor.process` - Basic and Error States.**
        *   **Test 3.1: Empty or whitespace content (raises `ContentProcessingError`).**
        *   **Test 3.2: Content too long (raises `ContentProcessingError`).**
        *   **Test 3.3: Content too short (raises `ContentProcessingError`).**
        *   **Test 3.4: General exception during HTML processing (e.g., mock `BeautifulSoup` to fail).**
        *   **Test 3.5: Fallback heading extraction on error.**
    *   **Sub-Task 4: Test `ContentProcessor.process` - Content Type and Format Handling.**
        *   **Test 4.1: Content type detection when `content_type` is `None` (mock `ContentTypeDetector`).**
        *   **Test 4.2: Successful processing by a non-HTML handler (e.g., Markdown - mock `FormatDetector` and the specific handler).**
        *   **Test 4.3: Error in non-HTML handler, fallback to HTML processing (mock handler to raise error, check HTML path is taken).**
    *   **Sub-Task 5: Test `ContentProcessor.process` - HTML Processing Details.**
        *   **Test 5.1: Removal of `script`, `style`, `noscript`, `iframe` tags.**
        *   **Test 5.2: Bleach sanitization (e.g., `extract_comments=True/False` affecting `strip_comments` arg to `bleach.clean`).**
        *   **Test 5.3: Base URL determination logic (no base URL, base URL from input, base URL from `<base>` tag, combination).**
        *   **Test 5.4: Metadata, Asset, Structure, Heading extraction (enabled/disabled via config).**
        *   **Test 5.5: Fallback heading extraction if `structure_handler.extract_headings` returns empty.**
        *   **Test 5.6: Structure creation from headings if `structure_handler.extract_structure` returns empty but headings exist.**
    *   **Sub-Task 6: Test `ContentProcessor.configure`.**
        *   **Test 6.1: Update various config attributes.**
        *   **Test 6.2: Ignoring `blocked_attributes` in input config.**
        *   **Test 6.3: Re-initialization of `CodeHandler` and `StructureHandler` when `code_languages` or `max_heading_level` change.**
        *   **Test 6.4: Edge case: `configure` called when `code_handler` is not yet initialized (ensure graceful handling/logging).**
    *   **Sub-Task 7: Test `add_content_filter`, `add_url_filter`, `add_metadata_extractor` (verify appends).**