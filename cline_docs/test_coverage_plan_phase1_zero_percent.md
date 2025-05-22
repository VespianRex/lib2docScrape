# Test Coverage Improvement Plan - Phase 1: 0% Coverage

Last Updated: 2025-05-21 15:25

## Overall Strategy
For each file with less than 100% coverage:
1.  Identify all lines and branches marked as "Missing" in the coverage report.
2.  For each missed line/branch, determine the specific condition or code path that was not executed.
3.  Propose new test cases or modifications to existing tests to cover these missed paths. Test cases should include:
    *   **Inputs:** Specific values or mock objects needed to trigger the code path.
    *   **Expected Outputs/Behavior:** What the code should do when that path is executed.
    *   **Edge Cases:** Consider null inputs, empty values, error conditions, and boundary values relevant to the missed code.
    *   **Test Logic (Pseudocode):** Outline the steps the test will perform.
4.  Structure these as sub-tasks that can be assigned for implementation.

---

## Phase 1 Details: Files with 0% Coverage

### File: `src/base.py`
*   **Coverage:** 0%
*   **Missed Lines:** 3-6
*   **Analysis:** This file likely defines a base class or interface.

**[x] Completed: No testable code remains in src/base.py (only imports and comments). No tests required.**

*   **Proposed Test Cases Sub-task:** (Obsolete)
    *   **Task:** Create tests for `src/base.py`.
    *   **Details & Test Logic:** (No longer applicable)

---

### File: `src/crawler.py`
*   **Coverage:** 0%
*   **Missed Lines:** 1-1034 (All lines)
*   **Analysis:** Main `DocumentationCrawler` class and its associated data models. This is critical.
*   **Proposed Test Cases Sub-tasks (grouped by class/major functionality with detailed logic):**

    1.  **[x] Completed: Test `CrawlTarget` Model (`src/crawler.py:36`)**
        *   **Details & Test Logic:**
            *   **Test 1.1: Default Instantiation**
                ```pseudocode
                target = CrawlTarget()
                ASSERT target.url == "https://docs.python.org/3/"
                ASSERT target.depth == 1
                // ... assert other defaults
                ```
            *   **Test 1.2: Custom Value Instantiation**
                ```pseudocode
                custom_values = {url: "http://example.com", depth: 2, ...}
                target = CrawlTarget(**custom_values)
                ASSERT target.url == "http://example.com"
                // ... assert other custom values
                ```
            *   **Test 1.3: Pydantic Validation (e.g., invalid type for depth)**
                ```pseudocode
                TRY CrawlTarget(depth="not_an_int")
                ASSERT pytest.raises(ValidationError) // Pydantic's error
                ```

    2.  **[x] Completed: Test `CrawlStats` Model (`src/crawler.py:48`)**
        *   **Details & Test Logic:**
            *   **Test 2.1: Default Instantiation (focus on `start_time`)**
                ```pseudocode
                stats = CrawlStats()
                ASSERT isinstance(stats.start_time, datetime)
                ASSERT stats.pages_crawled == 0
                // ... assert other defaults
                ```
            *   **Test 2.2: Setting and Getting Values**
                ```pseudocode
                stats = CrawlStats()
                stats.pages_crawled = 10
                stats.end_time = datetime.now(UTC)
                ASSERT stats.pages_crawled == 10
                ASSERT isinstance(stats.end_time, datetime)
                ```

    3.  **Task: Test `CrawlResult` Model (`src/crawler.py:61`)**
        *   **Details & Test Logic:**
            *   **Test 3.1: Instantiation with Required Fields**
                ```pseudocode
                mock_target = CrawlTarget()
                mock_stats = CrawlStats()
                result = CrawlResult(target=mock_target, stats=mock_stats, documents=[], issues=[], metrics={})
                ASSERT result.target == mock_target
                ASSERT result.failed_urls == [] // Check default factory
                ASSERT result.errors == {}     // Check default factory
                ```
            *   **Test 3.2: `arbitrary_types_allowed` for `Exception` in `errors`**
                ```pseudocode
                mock_target = CrawlTarget()
                mock_stats = CrawlStats()
                my_exception = ValueError("Test error")
                result = CrawlResult(target=mock_target, stats=mock_stats, documents=[], issues=[], metrics={}, errors={"http://example.com": my_exception})
                ASSERT result.errors["http://example.com"] == my_exception
                ```

    4.  **Task: Test `CrawlerConfig` Model (`src/crawler.py:80`)**
        *   **Details & Test Logic:** (Similar to `CrawlTarget` tests: default instantiation, custom values, Pydantic validation for field types/constraints if any).

    5.  **Task: Test `DocumentationCrawler.__init__` (`src/crawler.py:100`)**
        *   **Details & Test Logic:**
            *   **Test 5.1: Default Initialization**
                ```pseudocode
                crawler = DocumentationCrawler()
                ASSERT isinstance(crawler.config, CrawlerConfig)
                ASSERT isinstance(crawler.backend_selector, BackendSelector)
                ASSERT "http" in crawler.backend_selector._backends // Check HTTPBackend registration
                ASSERT crawler.direct_backend IS None
                ```
            *   **Test 5.2: Initialization with Custom Components**
                ```pseudocode
                mock_config = CrawlerConfig(concurrent_requests=5)
                mock_selector = Mock(spec=BackendSelector)
                mock_selector._backends = {} // Simulate initial state for registration check
                mock_processor = Mock(spec=ContentProcessor)
                
                crawler = DocumentationCrawler(config=mock_config, backend_selector=mock_selector, content_processor=mock_processor)
                ASSERT crawler.config.concurrent_requests == 5
                ASSERT crawler.backend_selector == mock_selector
                ASSERT "http" in crawler.backend_selector._backends // HTTPBackend should still be registered
                ```
            *   **Test 5.3: Initialization with Specific `backend`**
                ```pseudocode
                mock_backend = Mock(spec=CrawlerBackend, name="test_backend")
                crawler = DocumentationCrawler(backend=mock_backend)
                ASSERT crawler.direct_backend == mock_backend
                ASSERT crawler.backend == mock_backend
                ```

    6.  **Task: Test `DocumentationCrawler._find_links_recursive` (`src/crawler.py:182`)**
        *   **Details & Test Logic:**
            *   **Test 6.1: Empty Structure**
                ```pseudocode
                crawler = DocumentationCrawler()
                links = crawler._find_links_recursive({})
                ASSERT links == []
                links = crawler._find_links_recursive([])
                ASSERT links == []
                ```
            *   **Test 6.2: Simple Link**
                ```pseudocode
                structure = {'type': 'link', 'href': 'page1.html'}
                links = crawler._find_links_recursive(structure)
                ASSERT links == ['page1.html']
                ```
            *   **Test 6.3: Nested Structure with Multiple Links**
                ```pseudocode
                structure = {
                    'type': 'section', 
                    'content': [
                        {'type': 'link', 'href': 'page2.html'},
                        {'type': 'paragraph', 'children': [{'type': 'link_inline', 'href': 'page3.html'}]}
                    ],
                    'footer': {'type': 'link', 'href': 'page4.html'}
                }
                links = crawler._find_links_recursive(structure)
                ASSERT sorted(links) == sorted(['page2.html', 'page3.html', 'page4.html'])
                ```
            *   **Test 6.4: Structure without Links**
                ```pseudocode
                structure = {'type': 'paragraph', 'text': 'No links here'}
                links = crawler._find_links_recursive(structure)
                ASSERT links == []
                ```

    7.  **Task: Test `DocumentationCrawler._should_crawl_url` (`src/crawler.py:199`)**
        *   **Details & Test Logic (using `create_url_info` for inputs):**
            *   **Test 7.1: Invalid URL**
                ```pseudocode
                crawler = DocumentationCrawler()
                target_config = CrawlTarget(url="http://base.com")
                invalid_url_info = create_url_info("htp://badscheme.com") 
                ASSERT crawler._should_crawl_url(invalid_url_info, target_config) IS False
                ```
            *   **Test 7.2: Already Crawled URL**
                ```pseudocode
                crawler = DocumentationCrawler()
                target_config = CrawlTarget(url="http://base.com")
                url_info = create_url_info("http://base.com/page1")
                crawler._crawled_urls.add(url_info.normalized_url)
                ASSERT crawler._should_crawl_url(url_info, target_config) IS False
                ```
            *   **Test 7.3: Non-HTTP/S/File Scheme**
                ```pseudocode
                crawler = DocumentationCrawler()
                target_config = CrawlTarget(url="http://base.com")
                ftp_url_info = create_url_info("ftp://example.com/file.txt")
                ASSERT crawler._should_crawl_url(ftp_url_info, target_config) IS False
                ```
            *   **Test 7.4: External URL, `follow_external=False`**
                ```pseudocode
                crawler = DocumentationCrawler()
                target_config = CrawlTarget(url="http://internal.com", follow_external=False)
                external_url_info = create_url_info("http://external.com")
                ASSERT crawler._should_crawl_url(external_url_info, target_config) IS False
                // Test different schemes (http vs https on external)
                // Test file vs http
                ```
            *   **Test 7.5: External URL, `follow_external=True`**
                ```pseudocode
                crawler = DocumentationCrawler()
                target_config = CrawlTarget(url="http://internal.com", follow_external=True)
                external_url_info = create_url_info("http://external.com")
                ASSERT crawler._should_crawl_url(external_url_info, target_config) IS True 
                ```
            *   **Test 7.6: Internal URL (same registered domain)**
                ```pseudocode
                crawler = DocumentationCrawler()
                target_config = CrawlTarget(url="http://internal.com/path/", follow_external=False)
                internal_page_info = create_url_info("http://internal.com/another/page.html")
                ASSERT crawler._should_crawl_url(internal_page_info, target_config) IS True
                // Test http -> https upgrade for same domain
                https_internal_page_info = create_url_info("https://internal.com/another/page.html")
                ASSERT crawler._should_crawl_url(https_internal_page_info, target_config) IS True
                ```
            *   **Test 7.7: Exclude Patterns**
                ```pseudocode
                crawler = DocumentationCrawler()
                target_config = CrawlTarget(url="http://example.com", exclude_patterns=["/api/"])
                api_url_info = create_url_info("http://example.com/api/data")
                ASSERT crawler._should_crawl_url(api_url_info, target_config) IS False
                non_api_url_info = create_url_info("http://example.com/docs/data")
                ASSERT crawler._should_crawl_url(non_api_url_info, target_config) IS True
                ```
            *   **Test 7.8: Required Patterns**
                ```pseudocode
                crawler = DocumentationCrawler()
                target_config = CrawlTarget(url="http://example.com", required_patterns=["/docs/"])
                docs_url_info = create_url_info("http://example.com/docs/page1")
                ASSERT crawler._should_crawl_url(docs_url_info, target_config) IS True
                other_url_info = create_url_info("http://example.com/blog/post1")
                ASSERT crawler._should_crawl_url(other_url_info, target_config) IS False
                ```
            *   **Test 7.9: Allowed Paths**
                ```pseudocode
                crawler = DocumentationCrawler()
                target_config = CrawlTarget(url="http://example.com", allowed_paths=["/docs/", "/guides/"])
                allowed_url_info = create_url_info("http://example.com/docs/setup")
                ASSERT crawler._should_crawl_url(allowed_url_info, target_config) IS True
                disallowed_url_info = create_url_info("http://example.com/api/v1")
                ASSERT crawler._should_crawl_url(disallowed_url_info, target_config) IS False
                ```
            *   **Test 7.10: Excluded Paths**
                ```pseudocode
                crawler = DocumentationCrawler()
                target_config = CrawlTarget(url="http://example.com", excluded_paths=["/archive/"])
                excluded_url_info = create_url_info("http://example.com/archive/old-doc")
                ASSERT crawler._should_crawl_url(excluded_url_info, target_config) IS False
                normal_url_info = create_url_info("http://example.com/current/doc")
                ASSERT crawler._should_crawl_url(normal_url_info, target_config) IS True
                ```
            *   **Test 7.11: File Scheme URLs**
                ```pseudocode
                crawler = DocumentationCrawler()
                target_config = CrawlTarget(url="file:///base/path/index.html", follow_external=False)
                internal_file_info = create_url_info("file:///base/path/other.html")
                ASSERT crawler._should_crawl_url(internal_file_info, target_config) IS True
                // If target is file, and follow_external=False, http should be skipped
                http_url_info = create_url_info("http://example.com")
                ASSERT crawler._should_crawl_url(http_url_info, target_config) IS False
                ```

    8.  **Task: Test `DocumentationCrawler._fetch_and_process_with_backend` (`src/crawler.py:273`)**
        *   **Details & Test Logic (mock `CrawlerBackend`, `ContentProcessor`):**
            *   **Test 8.1: Successful Fetch and Process**
                ```pseudocode
                mock_backend = AsyncMock(spec=CrawlerBackend)
                mock_backend.crawl.return_value = BackendCrawlResult(url="http://example.com/page", status=200, content={"html": "<html></html>"}, metadata={"headers": {"Content-Type": "text/html"}})
                mock_processor = AsyncMock(spec=ContentProcessor)
                mock_processor.process.return_value = ProcessedContent(text_content="Hello", structure=[])
                
                crawler = DocumentationCrawler()
                url_info_obj = create_url_info("http://example.com/page")
                target_cfg = CrawlTarget(content_types=["text/html"])
                stats_obj = CrawlStats()
                visited = set()
                
                processed_content, backend_res, final_url = await crawler._fetch_and_process_with_backend(mock_backend, url_info_obj, target_cfg, stats_obj, visited)
                
                ASSERT processed_content IS NOT None
                ASSERT processed_content.text_content == "Hello"
                ASSERT backend_res.status == 200
                ASSERT final_url == url_info_obj.normalized_url
                ASSERT stats_obj.successful_crawls == 1
                ASSERT stats_obj.pages_crawled == 1
                ASSERT stats_obj.bytes_processed == len("<html></html>")
                mock_backend.crawl.assert_called_once_with(url_info=url_info_obj, config=crawler.config)
                mock_processor.process.assert_called_once_with("<html></html>", base_url=url_info_obj.normalized_url)
                ```
            *   **Test 8.2: Backend Crawl Fails (status != 200)**
                ```pseudocode
                mock_backend.crawl.return_value = BackendCrawlResult(url="http://example.com/page", status=404, error="Not Found")
                // ... setup other mocks and call _fetch_and_process_with_backend
                ASSERT processed_content IS None
                ASSERT backend_res.status == 404
                ASSERT final_url IS None
                ASSERT stats_obj.successful_crawls == 0 // Not incremented on failure
                ```
            *   **Test 8.3: Redirect to New, Unvisited URL**
                ```pseudocode
                original_url = "http://example.com/old"
                redirected_url = "http://example.com/new"
                mock_backend.crawl.return_value = BackendCrawlResult(url=redirected_url, status=200, content={"html": "<p>New</p>"}, metadata={"headers": {"Content-Type": "text/html"}})
                // ... setup, call with original_url_info
                ASSERT final_url == create_url_info(redirected_url).normalized_url
                ASSERT create_url_info(redirected_url).normalized_url in visited
                ```
            *   **Test 8.4: Redirect to Already Visited URL**
                ```pseudocode
                original_url = "http://example.com/old"
                redirected_url = "http://example.com/visited"
                visited.add(create_url_info(redirected_url).normalized_url)
                mock_backend.crawl.return_value = BackendCrawlResult(url=redirected_url, status=200, content={"html": "<p>Visited</p>"}, metadata={"headers": {"Content-Type": "text/html"}})
                // ... setup, call with original_url_info
                ASSERT processed_content IS None // Skipped
                ASSERT final_url == create_url_info(redirected_url).normalized_url
                ```
            *   **Test 8.5: Non-Allowed Content Type**
                ```pseudocode
                mock_backend.crawl.return_value = BackendCrawlResult(url="http://example.com/image.jpg", status=200, content={"html": ""}, metadata={"headers": {"Content-Type": "image/jpeg"}})
                target_cfg = CrawlTarget(content_types=["text/html"]) // Only HTML allowed
                // ... setup, call
                ASSERT processed_content IS None // Skipped
                ASSERT final_url == create_url_info("http://example.com/image.jpg").normalized_url
                ```

    9.  **Task: Test `DocumentationCrawler._process_url` (`src/crawler.py:353`)**
        *   **Details & Test Logic (extensive mocking of `_fetch_and_process_with_backend`, `_process_file_url`, `URLInfo`, backends, `RateLimiter`):**
            *   **Test 9.1: Max Pages Limit Reached**
                ```pseudocode
                crawler = DocumentationCrawler()
                target_cfg = CrawlTarget(max_pages=1)
                stats_obj = CrawlStats()
                visited = {"http://example.com/page0"} // Already 1 page visited
                
                result, new_links, metrics = await crawler._process_url("http://example.com/page1", 0, target_cfg, stats_obj, visited)
                ASSERT result IS None
                ASSERT new_links == []
                ```
            *   **Test 9.2: Invalid or Already Visited URL (early exit)**
                ```pseudocode
                // ... setup crawler, target_cfg, stats_obj
                visited = {"http://example.com/page1_normalized"}
                // Mock create_url_info to return normalized_url = "http://example.com/page1_normalized"
                result, new_links, metrics = await crawler._process_url("http://example.com/page1", 0, target_cfg, stats_obj, visited)
                ASSERT result IS None
                ```
            *   **Test 9.3: File URL Path (delegates to `_process_file_url`)**
                ```pseudocode
                crawler = DocumentationCrawler()
                crawler._process_file_url = AsyncMock(return_value=(Mock(spec=CrawlResult), [], {}))
                // ... setup target_cfg, stats_obj, visited
                await crawler._process_url("file:///path/to/file.html", 0, target_cfg, stats_obj, visited)
                crawler._process_file_url.assert_called_once()
                ```
            *   **Test 9.4: No Suitable Backend Found**
                ```pseudocode
                crawler = DocumentationCrawler()
                crawler.backend_selector.get_backend = AsyncMock(return_value=None) // No backend
                // ... setup target_cfg, stats_obj, visited
                result, new_links, metrics = await crawler._process_url("http://example.com/page1", 0, target_cfg, stats_obj, visited)
                ASSERT result IS NOT None
                ASSERT result.issues[0].message.startswith("No backend for")
                ASSERT stats_obj.failed_crawls == 1
                ```
            *   **Test 9.5: Successful Processing (first attempt, via `_fetch_and_process_with_backend`)**
                ```pseudocode
                crawler = DocumentationCrawler()
                mock_processed_content = ProcessedContent(text_content="Success", structure=[{'type':'link', 'href':'link1.html'}], title="Title")
                mock_backend_result = BackendCrawlResult(url="http://example.com/page1", status=200, content={"html":"..."}, metadata={})
                crawler._fetch_and_process_with_backend = AsyncMock(return_value=(mock_processed_content, mock_backend_result, "http://example.com/page1_normalized"))
                crawler.quality_checker.check = Mock(return_value=([], {})) // No quality issues
                crawler._find_links_recursive = Mock(return_value=["link1.html"])
                // ... setup target_cfg, stats_obj, visited
                
                result, new_links, metrics = await crawler._process_url("http://example.com/page1", 0, target_cfg, stats_obj, visited)
                
                ASSERT result IS NOT None
                ASSERT result.documents[0]["title"] == "Title"
                ASSERT new_links == [("http://example.com/link1.html", 1)] // Assuming base URL is http://example.com/
                crawler._fetch_and_process_with_backend.assert_called_once()
                ```
            *   **Test 9.6: Processing Fails After Retries (via `_fetch_and_process_with_backend` returning errors)**
                ```pseudocode
                crawler = DocumentationCrawler(config=CrawlerConfig(max_retries=2))
                error_backend_result = BackendCrawlResult(url="http://example.com/page1", status=500, error="Server Error")
                crawler._fetch_and_process_with_backend = AsyncMock(side_effect=[
                    (None, error_backend_result, None), # Attempt 1 fails
                    (None, error_backend_result, None)  # Attempt 2 fails
                ])
                // ... setup target_cfg, stats_obj, visited
                
                result, new_links, metrics = await crawler._process_url("http://example.com/page1", 0, target_cfg, stats_obj, visited)
                
                ASSERT result IS NOT None
                ASSERT result.issues[0].message.startswith("Failed after retries")
                ASSERT stats_obj.failed_crawls == 1
                ASSERT crawler._fetch_and_process_with_backend.call_count == 2
                ```
            *   **Test 9.7: `_fetch_and_process_with_backend` indicates skip (e.g., redirect loop)**
                ```pseudocode
                crawler = DocumentationCrawler()
                mock_backend_result = BackendCrawlResult(url="http://example.com/redirected_visited", status=200)
                crawler._fetch_and_process_with_backend = AsyncMock(return_value=(None, mock_backend_result, "http://example.com/redirected_visited_normalized")) // Skipped
                // ... setup
                result, new_links, metrics = await crawler._process_url("http://example.com/page1", 0, target_cfg, stats_obj, visited)
                ASSERT result IS None
                ```
            *   **Test 9.8: Rate Limiting Logic (mock `RateLimiter.acquire` and `asyncio.sleep`)**
                ```pseudocode
                crawler = DocumentationCrawler()
                crawler.rate_limiter.acquire = AsyncMock(return_value=0.1) // Simulate wait time
                asyncio_sleep_mock = AsyncMock() 
                // Patch asyncio.sleep to use asyncio_sleep_mock
                // ... setup successful processing mocks for _fetch_and_process_with_backend
                
                await crawler._process_url("http://example.com/page1", 0, target_cfg, stats_obj, visited)
                crawler.rate_limiter.acquire.assert_called_once()
                asyncio_sleep_mock.assert_called_once_with(0.1)
                ```
            *   **Test 9.9: Link Discovery and Depth Increment**
                ```pseudocode
                // ... setup for successful processing as in 9.5
                // Ensure _find_links_recursive returns multiple links, some relative, some absolute
                // Ensure sanitize_and_join_url is correctly used
                // Check that new_links contains tuples of (absolute_url, current_depth + 1)
                ```

    10. **Task: Test `DocumentationCrawler._process_file_url` (`src/crawler.py:874`)**
        *   **Details & Test Logic (mock `os.path`, `open`, `ContentProcessor`, `QualityChecker`):**
            *   **Test 10.1: File Not Found**
                ```pseudocode
                crawler = DocumentationCrawler()
                mock_url_info = create_url_info("file:///path/to/nonexistent.html")
                // Mock os.path.exists to return False
                // ... setup target_cfg, stats_obj
                result, new_links, metrics = await crawler._process_file_url(mock_url_info, 0, target_cfg, stats_obj)
                ASSERT result.issues[0].message.startswith("File not found")
                ASSERT stats_obj.failed_crawls == 1
                ```
            *   **Test 10.2: Path is Directory**
                ```pseudocode
                // Mock os.path.exists to True, os.path.isdir to True
                // ... setup and call
                ASSERT result.issues[0].message.startswith("Path is a directory")
                ```
            *   **Test 10.3: Successful File Read and Process**
                ```pseudocode
                // Mock os.path.exists True, os.path.isdir False
                // Mock open() to return a mock file object with read() method
                // Mock content_processor.process to return ProcessedContent
                // Mock quality_checker.check to return no issues
                // Mock _find_links_recursive
                // ... setup and call
                ASSERT result.documents[0]["content"] == "Mocked file content"
                ASSERT stats_obj.successful_crawls == 1
                ASSERT new_links are correctly formed
                ```
            *   **Test 10.4: File Read Error (IOError)**
                ```pseudocode
                // Mock open() to raise IOError
                // ... setup and call
                ASSERT result.issues[0].message.contains("Error reading file")
                ```
            *   **Test 10.5: Content Processor Error**
                ```pseudocode
                // Mock content_processor.process to raise an Exception
                // ... setup and call
                ASSERT result.issues[0].message.contains("Error processing file content")
                ```

    11. **Task: Test `DocumentationCrawler._initialize_crawl_queue` (`src/crawler.py:585`)**
        *   **Details & Test Logic (mock `ProjectIdentifier`, `DuckDuckGoSearch`):**
            *   **Test 11.1: Valid Target URL, No DuckDuckGo**
                ```pseudocode
                crawler = DocumentationCrawler(config=CrawlerConfig(use_duckduckgo=False))
                target_cfg = CrawlTarget(url="http://example.com/start")
                queue, initial_url = await crawler._initialize_crawl_queue(target_cfg)
                ASSERT len(queue) == 1
                ASSERT queue[0] == ("http://example.com/start", 0)
                ASSERT initial_url == "http://example.com/start"
                ```
            *   **Test 11.2: Valid Target URL, With DuckDuckGo, Project Identified**
                ```pseudocode
                crawler = DocumentationCrawler(config=CrawlerConfig(use_duckduckgo=True))
                crawler.project_identifier.identify = Mock(return_value=ProjectIdentity(name="TestLib", type=ProjectType.LIBRARY, version="1.0"))
                crawler.duckduckgo.search_for_project_docs = AsyncMock(return_value=["http://ddg.com/testlib/docs"])
                target_cfg = CrawlTarget(url="http://example.com/start") // This might be ignored if DDG provides results
                
                queue, initial_url = await crawler._initialize_crawl_queue(target_cfg)
                ASSERT "http://ddg.com/testlib/docs" in [item[0] for item in queue]
                // Check if target.url is also added or if DDG results replace it based on logic
                ```
            *   **Test 11.3: DuckDuckGo Enabled, No Project Identified or No DDG Results**
                ```pseudocode
                crawler.project_identifier.identify = Mock(return_value=None) // Or DDG search returns []
                // ... setup and call
                ASSERT queue[0][0] == target_cfg.url // Fallback to target.url
                ```
            *   **Test 11.4: Invalid Target URL (should raise error or handle gracefully)**
                ```pseudocode
                target_cfg = CrawlTarget(url="invalid-url-scheme")
                // Expect create_url_info to mark it invalid
                // Assert behavior (e.g., empty queue, specific error logged/raised)
                ```

    12. **Task: Test `DocumentationCrawler.crawl` (Integration) (`src/crawler.py:629`)**
        *   **Details & Test Logic (High-level integration, mock external calls like `_initialize_crawl_queue`, `_process_url`, `cleanup`):**
            *   **Test 12.1: Simple Successful Crawl (1 page, depth 0)**
                ```pseudocode
                crawler = DocumentationCrawler()
                target_cfg = CrawlTarget(url="http://example.com/page1", depth=0)
                
                // Mock _initialize_crawl_queue to return a queue with ("http://example.com/page1", 0)
                // Mock _process_url to return a successful CrawlResult for page1, with no new links
                // Mock cleanup to be callable
                
                final_result = await crawler.crawl(target_cfg)
                
                ASSERT final_result.stats.pages_crawled == 1
                ASSERT final_result.stats.successful_crawls == 1
                ASSERT len(final_result.documents) == 1
                // Assert _process_url was called once with correct args
                // Assert cleanup was called
                ```
            *   **Test 12.2: Depth Limited Crawl (e.g., depth 1, finds new links)**
                ```pseudocode
                // Mock _initialize_crawl_queue for initial URL
                // Mock _process_url for initial URL to return a CrawlResult with new_links = [("http://example.com/page2", 1)]
                // Mock _process_url for page2 to return a CrawlResult with no new links (depth limit reached for its children)
                // ... call crawl with depth=1
                ASSERT final_result.stats.pages_crawled == 2
                ```
            *   **Test 12.3: `max_pages` Limit Hit**
                ```pseudocode
                target_cfg = CrawlTarget(url="http://example.com/page1", depth=5, max_pages=2)
                // Mock _process_url to always find new links, but ensure it's only called twice
                // ... call crawl
                ASSERT final_result.stats.pages_crawled == 2
                ```
            *   **Test 12.4: `asyncio.TimeoutError` during `_process_url`**
                ```pseudocode
                crawler._process_url = AsyncMock(side_effect=asyncio.TimeoutError)
                // ... call crawl
                ASSERT "Crawl timed out" in final_result.issues[0].message
                ```
            *   **Test 12.5: Error in `_process_url`**
                ```pseudocode
                // Mock _process_url to return a CrawlResult with errors/issues
                // ... call crawl
                ASSERT len(final_result.issues) > 0
                ASSERT final_result.stats.failed_crawls > 0
                ```

    13. **Task: Test `DocumentationCrawler._setup_backends` (`src/crawler.py:843`)**
        *   **Details & Test Logic:**
            *   **Test 13.1: Execution without Error**
                ```pseudocode
                crawler = DocumentationCrawler()
                TRY crawler._setup_backends()
                ASSERT no exception was raised
                // If it's supposed to do something in the future, tests would change.
                ```

    14. **Task: Test `DocumentationCrawler.cleanup` (`src/crawler.py:990`)**
        *   **Details & Test Logic:**
            *   **Test 14.1: Cleanup Called on Registered Backends**
                ```pseudocode
                mock_backend1 = AsyncMock(spec=CrawlerBackend)
                mock_backend1.cleanup = AsyncMock()
                mock_backend2 = AsyncMock(spec=CrawlerBackend) // No cleanup method
                
                crawler = DocumentationCrawler()
                crawler.backend_selector.register_backend("b1", mock_backend1, BackendCriteria())
                crawler.backend_selector.register_backend("b2", mock_backend2, BackendCriteria())
                
                await crawler.cleanup()
                mock_backend1.cleanup.assert_called_once()
                ```
            *   **Test 14.2: Cleanup Called on Direct Backend**
                ```pseudocode
                mock_direct_backend = AsyncMock(spec=CrawlerBackend)
                mock_direct_backend.cleanup = AsyncMock()
                crawler = DocumentationCrawler(backend=mock_direct_backend)
                await crawler.cleanup()
                mock_direct_backend.cleanup.assert_called_once()
                ```

    15. **Task: Test `DocumentationCrawler._generate_search_queries` (`src/crawler.py:1002`)**
        *   **Details & Test Logic:**
            *   **Test 15.1: Library with Version**
                ```pseudocode
                crawler = DocumentationCrawler()
                identity = ProjectIdentity(name="MyLib", type=ProjectType.LIBRARY, version="1.2.3")
                queries = crawler._generate_search_queries("http://example.com/mylib/1.2.3/docs", identity)
                ASSERT "MyLib 1.2.3 documentation" in queries
                ASSERT "MyLib 1.2 documentation" in queries // Major.minor
                ASSERT "MyLib documentation" in queries
                ```
            *   **Test 15.2: Library without Version**
                ```pseudocode
                identity = ProjectIdentity(name="MyLib", type=ProjectType.LIBRARY, version=None)
                queries = crawler._generate_search_queries("http://example.com/mylib/docs", identity)
                ASSERT queries == ["MyLib documentation"]
                ```
            *   **Test 15.3: Non-Library Project Type**
                ```pseudocode
                identity = ProjectIdentity(name="MyFramework", type=ProjectType.FRAMEWORK, version="2.0")
                queries = crawler._generate_search_queries("http://example.com/myframework/docs", identity)
                ASSERT queries == ["MyFramework 2.0 documentation", "MyFramework documentation"]
                ```
            *   **Test 15.4: `AttributeError` during version parsing (e.g., version is not string-like)**
                ```pseudocode
                identity = ProjectIdentity(name="MyLib", type=ProjectType.LIBRARY, version=123) // Invalid version type
                queries = crawler._generate_search_queries("http://example.com/mylib/docs", identity)
                ASSERT queries == ["MyLib documentation"] // Falls back gracefully
                ```

---

### File: `src/ui/doc_viewer_complete.py`
*   **Coverage:** 0%
*   **Missed Lines:** 6-348 (All functional lines)
*   **Analysis:** FastAPI application for viewing documentation.
*   **Proposed Test Cases Sub-tasks (with detailed logic):**

    1.  **Task: Test Pydantic Models (`VersionInfo`, `DocumentInfo`, `DiffRequest`, `SearchRequest`) (`src/ui/doc_viewer_complete.py:26`)**
        *   **Details & Test Logic:**
            *   **Test 1.1: `VersionInfo` Instantiation**
                ```pseudocode
                data = {"version": "1.0", "doc_url": "http://a.com", "crawl_date": datetime.now()}
                info = VersionInfo(**data)
                ASSERT info.version == "1.0"
                // Test with optional fields (release_date, changes) present and absent
                ```
            *   **Test 1.2: `DocumentInfo` Instantiation**
                ```pseudocode
                data = {"title": "Intro", "url": "http://b.com", "content_type": "html", "content_format": "html", "last_updated": datetime.now(), "versions": ["1.0"], "topics": ["setup"]}
                info = DocumentInfo(**data)
                ASSERT info.title == "Intro"
                ```
            *   **Test 1.3: `DiffRequest` Instantiation**
                ```pseudocode
                data = {"library": "libA", "doc_path": "intro.md", "version1": "1.0", "version2": "1.1"}
                req = DiffRequest(**data)
                ASSERT req.format == "html" // Default value
                ```
            *   **Test 1.4: `SearchRequest` Instantiation**
                ```pseudocode
                data = {"query": "test"}
                req = SearchRequest(**data)
                ASSERT req.library IS None // Optional fields
                ```
            *   **Test 1.5: Pydantic Validation (e.g., missing required field)**
                ```pseudocode
                TRY VersionInfo(doc_url="http://a.com", crawl_date=datetime.now()) // Missing 'version'
                ASSERT pytest.raises(ValidationError)
                ```

    2.  **Task: Test `DocViewerApp.__init__` (`src/ui/doc_viewer_complete.py:68`)**
        *   **Details & Test Logic:**
            *   **Test 2.1: Default Initialization**
                ```pseudocode
                app_instance = DocViewerApp()
                ASSERT isinstance(app_instance.doc_organizer, DocOrganizer)
                ASSERT isinstance(app_instance.version_tracker, LibraryVersionTracker)
                ASSERT isinstance(app_instance.app, FastAPI)
                // Check if templates and static files are mounted (requires TestClient or inspecting app routes)
                ```
            *   **Test 2.2: Initialization with Custom Components**
                ```pseudocode
                mock_organizer = Mock(spec=DocOrganizer)
                app_instance = DocViewerApp(doc_organizer=mock_organizer, templates_dir="custom_templates")
                ASSERT app_instance.doc_organizer == mock_organizer
                // Assert templates directory is correctly set (inspect Jinja2Templates instance)
                ```

    3.  **Task: Test `DocViewerApp._get_libraries` (`src/ui/doc_viewer_complete.py:220`)**
        *   **Details & Test Logic (mock `version_tracker`):**
            *   **Test 3.1: Successful Retrieval**
                ```pseudocode
                mock_tracker = Mock(spec=LibraryVersionTracker)
                mock_tracker.get_libraries.return_value = ["libA", "libB"]
                app_instance = DocViewerApp(version_tracker=mock_tracker)
                libs = await app_instance._get_libraries()
                ASSERT libs == ["libA", "libB"]
                ```
            *   **Test 3.2: Empty List**
                ```pseudocode
                mock_tracker.get_libraries.return_value = []
                // ... call _get_libraries
                ASSERT libs == []
                ```
            *   **Test 3.3: Exception Handling**
                ```pseudocode
                mock_tracker.get_libraries.side_effect = Exception("DB error")
                // Patch 'handle_error' to check if it's called
                // ... call _get_libraries
                ASSERT libs == [] // Should return empty list on error
                // Assert handle_error was called with correct context
                ```

    4.  **Task: Test `DocViewerApp._get_library_versions` (`src/ui/doc_viewer_complete.py:238`)**
        *   **Details & Test Logic (mock `version_tracker`):**
            *   **Test 4.1: Successful Retrieval**
                ```pseudocode
                mock_tracker = Mock(spec=LibraryVersionTracker)
                # Mock VersionData objects returned by version_tracker.get_versions
                mock_version_data = [Mock(version="1.0", release_date=datetime.now(), doc_url="url1", crawl_date=datetime.now(), changes={})]
                mock_tracker.get_versions.return_value = mock_version_data
                app_instance = DocViewerApp(version_tracker=mock_tracker)
                
                versions_info = await app_instance._get_library_versions("libA")
                ASSERT len(versions_info) == 1
                ASSERT isinstance(versions_info[0], VersionInfo)
                ASSERT versions_info[0].version == "1.0"
                mock_tracker.get_versions.assert_called_once_with("libA")
                ```
            *   **Test 4.2: Empty List / Library Not Found**
                ```pseudocode
                mock_tracker.get_versions.return_value = []
                // ... call _get_library_versions
                ASSERT versions_info == []
                ```
            *   **Test 4.3: Exception Handling**
                ```pseudocode
                mock_tracker.get_versions.side_effect = Exception("Tracker error")
                // ... call _get_library_versions
                ASSERT versions_info == []
                // Assert handle_error was called
                ```

    5.  **Task: Test `DocViewerApp._get_version_docs` (`src/ui/doc_viewer_complete.py:270`)**
        *   **Details & Test Logic (mock `doc_organizer`):** (Similar structure to `_get_library_versions` tests, but mocking `doc_organizer.get_documents` and asserting `DocumentInfo` objects).

    6.  **Task: Test `DocViewerApp._get_document` (`src/ui/doc_viewer_complete.py:306`)**
        *   **Details & Test Logic (mock `doc_organizer`, `format_handler`):**
            *   **Test 6.1: Document Found (HTML format, no conversion needed)**
                ```pseudocode
                mock_organizer = Mock(spec=DocOrganizer)
                mock_doc_data = Mock(title="Doc Title", url="doc_url", content_type="text/html", format="html", last_updated=datetime.now(), versions=[], topics=[], summary="sum", content="<p>HTML Content</p>")
                mock_organizer.get_document.return_value = mock_doc_data
                app_instance = DocViewerApp(doc_organizer=mock_organizer)
                
                doc_details = await app_instance._get_document("libA", "1.0", "path/to/doc.html")
                ASSERT doc_details["title"] == "Doc Title"
                ASSERT doc_details["content"] == "<p>HTML Content</p>"
                # Assert format_handler.convert was NOT called
                ```
            *   **Test 6.2: Document Found (Markdown format, needs conversion)**
                ```pseudocode
                mock_doc_data.format = "markdown"
                mock_doc_data.content = "# MD Content"
                mock_formatter = Mock(spec=FormatHandler)
                mock_formatter.convert.return_value = "<h1>Converted MD Content</h1>"
                app_instance = DocViewerApp(doc_organizer=mock_organizer, format_handler=mock_formatter)
                
                doc_details = await app_instance._get_document("libA", "1.0", "path/to/doc.md")
                ASSERT doc_details["content"] == "<h1>Converted MD Content</h1>"
                mock_formatter.convert.assert_called_once_with("# MD Content", DocFormat.MARKDOWN, DocFormat.HTML)
                ```
            *   **Test 6.3: Document Not Found**
                ```pseudocode
                mock_organizer.get_document.return_value = None
                // ... call _get_document
                ASSERT doc_details IS None
                ```
            *   **Test 6.4: Exception Handling**
                ```pseudocode
                mock_organizer.get_document.side_effect = Exception("Organizer error")
                // ... call _get_document
                ASSERT doc_details IS None
                // Assert handle_error was called
                ```

    7.  **Task: Test `DocViewerApp` API Endpoints (Integration with `TestClient`) (`src/ui/doc_viewer_complete.py:106` onwards)**
        *   **Details & Test Logic:**
            *   **General Approach for each endpoint:**
                ```pseudocode
                client = TestClient(DocViewerApp(doc_organizer=mock_do, version_tracker=mock_vt).app) // Use mocked dependencies
                
                // For GET endpoints:
                response = client.get("/api/libraries")
                ASSERT response.status_code == 200
                ASSERT response.json() == {"libraries": ["expected_lib"]} // Based on mock_vt setup
                
                // For POST endpoints:
                response = client.post("/api/search", json={"query": "test"})
                ASSERT response.status_code == 200
                ASSERT "results" in response.json()
                
                // Test 404s:
                response = client.get("/api/library/nonexistent/versions")
                ASSERT response.status_code == 404
                ```
            *   **Specific Test Logic for `/` (home):**
                ```pseudocode
                // Mock _get_libraries to return some data
                response = client.get("/")
                ASSERT response.status_code == 200
                ASSERT "text/html" in response.headers["content-type"]
                // Optionally, check for presence of key elements in HTML if stable
                ```
            *   **Specific Test Logic for `/api/diff`:**
                ```pseudocode
                // Mock the internal _get_diff method of DocViewerApp instance if it exists,
                // OR mock the dependencies it uses (e.g., version_tracker.get_diff_content)
                // to control its output.
                // Since _get_diff is not in the snippet, assume we mock its outcome.
                // For example, if _get_diff is part of DocViewerApp:
                // app_instance = DocViewerApp(...)
                // app_instance._get_diff = AsyncMock(return_value={"diff_html": "<div>...</div>"})
                // client = TestClient(app_instance.app)
                
                response = client.post("/api/diff", json={"library":"libA", "doc_path":"p", "version1":"v1", "version2":"v2"})
                ASSERT response.status_code == 200
                ASSERT response.json() == {"diff_html": "<div>...</div>"}
                // Test 404 if _get_diff (or its underlying logic) returns None/empty
                ```
            *   **(Repeat for all HTML and API endpoints: `/library/{library}`, `/library/{library}/version/{version}`, `/library/{library}/version/{version}/doc/{doc_path:path}`, `/diff`, `/search`, `/api/search`, `/api/libraries`, `/api/library/{library}/versions`, `/api/library/{library}/version/{version}/docs`. Mock their direct helper methods like `_get_libraries`, `_get_library_versions`, etc., or the deeper dependencies like `DocOrganizer` and `LibraryVersionTracker`.)**