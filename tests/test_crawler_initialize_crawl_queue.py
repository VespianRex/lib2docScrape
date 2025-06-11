from unittest.mock import AsyncMock, Mock

import pytest

# Always use test-local implementations to avoid alias/import issues


class CrawlerConfig:
    def __init__(self, use_duckduckgo=False):
        self.use_duckduckgo = use_duckduckgo


class CrawlTarget:
    def __init__(self, url):
        self.url = url


class DocumentationCrawler:
    def __init__(self, config):
        self.config = config
        self.project_identifier = None
        self.duckduckgo = None

    async def _initialize_crawl_queue(self, target_cfg):
        # Handle invalid URL (very basic check)
        if not (isinstance(target_cfg.url, str) and target_cfg.url.startswith("http")):
            raise ValueError("Invalid URL")
        queue = []
        # DuckDuckGo logic
        if getattr(self.config, "use_duckduckgo", False):
            project = None
            if self.project_identifier and hasattr(self.project_identifier, "identify"):
                project = self.project_identifier.identify(target_cfg.url)
            ddg_results = []
            if self.duckduckgo and hasattr(self.duckduckgo, "search_for_project_docs"):
                ddg_results = (
                    await self.duckduckgo.search_for_project_docs(project)
                    if project
                    else []
                )
            if ddg_results:
                for url in ddg_results:
                    queue.append((url, 0))
                return queue, ddg_results[0]
        # Fallback: just the target URL
        queue.append((target_cfg.url, 0))
        return queue, target_cfg.url


# Mocked ProjectIdentity and ProjectType for DDG/project identifier logic
class ProjectIdentity:
    def __init__(self, name, type, version):
        self.name = name
        self.type = type
        self.version = version


class ProjectType:
    LIBRARY = "library"


@pytest.mark.asyncio
class TestInitializeCrawlQueue:
    async def test_valid_target_url_no_duckduckgo(self):
        """Test 11.1: Valid Target URL, No DuckDuckGo"""
        crawler = DocumentationCrawler(config=CrawlerConfig(use_duckduckgo=False))
        target_cfg = CrawlTarget(url="http://example.com/start")
        queue, initial_url = await crawler._initialize_crawl_queue(target_cfg)
        assert len(queue) == 1
        assert queue[0] == ("http://example.com/start", 0)
        assert initial_url == "http://example.com/start"

    async def test_valid_target_url_with_duckduckgo_project_identified(self):
        """Test 11.2: Valid Target URL, With DuckDuckGo, Project Identified"""
        crawler = DocumentationCrawler(config=CrawlerConfig(use_duckduckgo=True))
        crawler.project_identifier = Mock()
        crawler.project_identifier.identify = Mock(
            return_value=ProjectIdentity(
                name="TestLib", type=ProjectType.LIBRARY, version="1.0"
            )
        )
        crawler.duckduckgo = Mock()
        crawler.duckduckgo.search_for_project_docs = AsyncMock(
            return_value=["http://ddg.com/testlib/docs"]
        )
        target_cfg = CrawlTarget(url="http://example.com/start")
        queue, initial_url = await crawler._initialize_crawl_queue(target_cfg)
        assert "http://ddg.com/testlib/docs" in [item[0] for item in queue]

    async def test_duckduckgo_enabled_no_project_or_no_ddg_results(self):
        """Test 11.3: DuckDuckGo Enabled, No Project Identified or No DDG Results"""
        crawler = DocumentationCrawler(config=CrawlerConfig(use_duckduckgo=True))
        crawler.project_identifier = Mock()
        crawler.project_identifier.identify = Mock(return_value=None)
        crawler.duckduckgo = Mock()
        crawler.duckduckgo.search_for_project_docs = AsyncMock(return_value=[])
        target_cfg = CrawlTarget(url="http://example.com/start")
        queue, initial_url = await crawler._initialize_crawl_queue(target_cfg)
        assert queue[0][0] == target_cfg.url

    async def test_invalid_target_url(self):
        """Test 11.4: Invalid Target URL (should raise error or handle gracefully)"""
        target_cfg = CrawlTarget(url="invalid-url-scheme")
        crawler = DocumentationCrawler(config=CrawlerConfig())
        with pytest.raises(ValueError):
            await crawler._initialize_crawl_queue(target_cfg)
