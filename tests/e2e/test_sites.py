"""Real-world test sites configuration and management.

This module defines test sites for automated real-world testing.
Sites are categorized by complexity, technology, and testing purpose.
"""

import asyncio
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import aiohttp
import pytest

logger = logging.getLogger(__name__)


class SiteCategory(Enum):
    """Categories of test sites based on complexity and purpose."""

    SIMPLE = "simple"  # Basic HTML sites
    DOCUMENTATION = "docs"  # Documentation sites
    SPA = "spa"  # Single Page Applications
    DYNAMIC = "dynamic"  # Sites with dynamic content
    LARGE = "large"  # Large sites for performance testing
    PROBLEMATIC = "problematic"  # Sites known to cause issues


class TechStack(Enum):
    """Technology stacks used by test sites."""

    STATIC_HTML = "static_html"
    WORDPRESS = "wordpress"
    REACT = "react"
    VUE = "vue"
    ANGULAR = "angular"
    GATSBY = "gatsby"
    NEXTJS = "nextjs"
    SPHINX = "sphinx"
    GITBOOK = "gitbook"
    MKDOCS = "mkdocs"


@dataclass
class TestSite:
    """Configuration for a test site."""

    name: str
    url: str
    category: SiteCategory
    tech_stack: TechStack
    expected_pages: int
    max_depth: int = 2
    timeout: int = 30
    description: str = ""
    known_issues: list[str] = None
    validation_rules: dict[str, any] = None

    def __post_init__(self):
        if self.known_issues is None:
            self.known_issues = []
        if self.validation_rules is None:
            self.validation_rules = {}


# Test site configurations
TEST_SITES = {
    # Simple sites for basic functionality testing
    "httpbin": TestSite(
        name="HTTPBin",
        url="https://httpbin.org/",
        category=SiteCategory.SIMPLE,
        tech_stack=TechStack.STATIC_HTML,
        expected_pages=5,
        max_depth=1,
        description="Simple HTTP testing service",
        validation_rules={
            "min_content_length": 100,
            "required_elements": ["title", "body"],
            "forbidden_errors": ["404", "500"],
        },
    ),
    "example_com": TestSite(
        name="Example.com",
        url="https://example.com/",
        category=SiteCategory.SIMPLE,
        tech_stack=TechStack.STATIC_HTML,
        expected_pages=1,
        max_depth=1,
        description="IANA example domain",
        validation_rules={
            "min_content_length": 50,
            "required_text": ["Example Domain"],
        },
    ),
    # Documentation sites
    "python_docs": TestSite(
        name="Python Documentation",
        url="https://docs.python.org/3/",
        category=SiteCategory.DOCUMENTATION,
        tech_stack=TechStack.SPHINX,
        expected_pages=20,
        max_depth=2,
        timeout=60,
        description="Official Python documentation",
        validation_rules={
            "min_content_length": 500,
            "required_elements": ["title", "nav", "main"],
            "required_text": ["Python", "documentation"],
        },
    ),
    "fastapi_docs": TestSite(
        name="FastAPI Documentation",
        url="https://fastapi.tiangolo.com/",
        category=SiteCategory.DOCUMENTATION,
        tech_stack=TechStack.MKDOCS,
        expected_pages=15,
        max_depth=2,
        description="FastAPI framework documentation",
        validation_rules={"min_content_length": 300, "required_text": ["FastAPI"]},
    ),
    # GitHub Pages sites
    "github_pages": TestSite(
        name="GitHub Pages Example",
        url="https://pages.github.com/",
        category=SiteCategory.SIMPLE,
        tech_stack=TechStack.STATIC_HTML,
        expected_pages=5,
        max_depth=1,
        description="GitHub Pages landing page",
    ),
    # Performance testing sites
    "wikipedia": TestSite(
        name="Wikipedia",
        url="https://en.wikipedia.org/wiki/Main_Page",
        category=SiteCategory.LARGE,
        tech_stack=TechStack.WORDPRESS,  # MediaWiki actually, but similar
        expected_pages=10,
        max_depth=1,
        timeout=45,
        description="Large content site for performance testing",
        known_issues=["Rate limiting", "Large page sizes"],
        validation_rules={"min_content_length": 1000, "required_text": ["Wikipedia"]},
    ),
}


class TestSiteManager:
    """Manages test sites and their availability."""

    def __init__(self):
        self.available_sites: set[str] = set()
        self.unavailable_sites: set[str] = set()
        self.last_check: Optional[float] = None

    async def check_site_availability(self, site: TestSite) -> bool:
        """Check if a test site is available."""
        try:
            async with aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10)
            ) as session:
                async with session.head(site.url) as response:
                    return response.status < 400
        except Exception as e:
            logger.warning(f"Site {site.name} unavailable: {e}")
            return False

    async def refresh_availability(self) -> dict[str, bool]:
        """Check availability of all test sites."""
        results = {}
        tasks = []

        for site_id, site in TEST_SITES.items():
            task = asyncio.create_task(self.check_site_availability(site))
            tasks.append((site_id, task))

        for site_id, task in tasks:
            try:
                is_available = await task
                results[site_id] = is_available
                if is_available:
                    self.available_sites.add(site_id)
                    self.unavailable_sites.discard(site_id)
                else:
                    self.unavailable_sites.add(site_id)
                    self.available_sites.discard(site_id)
            except Exception as e:
                logger.error(f"Error checking {site_id}: {e}")
                results[site_id] = False
                self.unavailable_sites.add(site_id)
                self.available_sites.discard(site_id)

        self.last_check = asyncio.get_event_loop().time()
        return results

    def get_sites_by_category(self, category: SiteCategory) -> list[TestSite]:
        """Get available sites by category."""
        return [
            site
            for site_id, site in TEST_SITES.items()
            if site.category == category and site_id in self.available_sites
        ]

    def get_available_sites(self) -> list[TestSite]:
        """Get all available test sites."""
        return [
            site
            for site_id, site in TEST_SITES.items()
            if site_id in self.available_sites
        ]


# Global site manager instance
site_manager = TestSiteManager()


@pytest.fixture(scope="session")
async def available_test_sites():
    """Pytest fixture to get available test sites."""
    await site_manager.refresh_availability()
    return site_manager.get_available_sites()


@pytest.fixture(scope="session")
async def simple_test_sites():
    """Pytest fixture for simple test sites."""
    await site_manager.refresh_availability()
    return site_manager.get_sites_by_category(SiteCategory.SIMPLE)


@pytest.fixture(scope="session")
async def documentation_sites():
    """Pytest fixture for documentation sites."""
    await site_manager.refresh_availability()
    return site_manager.get_sites_by_category(SiteCategory.DOCUMENTATION)
