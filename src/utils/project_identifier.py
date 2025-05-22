import logging
import re
from enum import Enum
from dataclasses import dataclass, field # Added field for default_factory
from typing import List, Optional

import aiohttp # Keep aiohttp import here

# --- Copied from src/crawler.py ---

class ProjectType(Enum):
    """Types of software projects that can be identified."""
    PACKAGE = "package"
    FRAMEWORK = "framework"
    PROGRAM = "program"
    LIBRARY = "library"
    CLI_TOOL = "cli_tool"
    WEB_APP = "web_app"
    API = "api"
    UNKNOWN = "unknown"

@dataclass
class ProjectIdentity:
    """Information about an identified project."""
    name: str
    type: ProjectType
    language: Optional[str] = None
    framework: Optional[str] = None
    repository: Optional[str] = None
    package_manager: Optional[str] = None
    main_doc_url: Optional[str] = None
    related_keywords: List[str] = field(default_factory=list) # Use field for default_factory
    confidence: float = 0.0

    # Removed __post_init__ as default_factory handles the list initialization

class ProjectIdentifier:
    """Identifies project type and provides relevant configuration."""

    def __init__(self):
        self.package_doc_urls = {}
        self.fallback_urls = {}

        # Common documentation patterns
        self.doc_patterns = [
            "https://{package}.readthedocs.io/en/latest/",
            "https://{package}.readthedocs.io/en/stable/",
            "https://docs.{package}.org/",
            "https://{package}.org/docs/",
            "https://www.{package}.org/docs/",
            "https://github.com/{package}/{package}/blob/main/README.md"
        ]

        self.language_patterns = {
            'python': [r'\.py$', r'requirements\.txt$', r'setup\.py$', r'pyproject\.toml$'],
            'javascript': [r'\.js$', r'package\.json$', r'node_modules'],
            'java': [r'\.java$', r'pom\.xml$', r'build\.gradle$'],
            'ruby': [r'\.rb$', r'Gemfile$'],
            'go': [r'\.go$', r'go\.mod$'],
            'rust': [r'\.rs$', r'Cargo\.toml$'],
            'php': [r'\.php$', r'composer\.json$'],
        }

        self.framework_patterns = {
            'django': [r'django', r'urls\.py$', r'wsgi\.py$'],
            'flask': [r'flask', r'app\.py$'],
            'react': [r'react', r'jsx$', r'tsx$'],
            'angular': [r'angular', r'component\.ts$'],
            'vue': [r'vue', r'vue-cli'],
            'spring': [r'spring-boot', r'springframework'],
            'rails': [r'rails', r'activerecord'],
        }

        self.doc_platforms = {
            'readthedocs.org': 0.9,
            'docs.python.org': 0.9,
            'developer.mozilla.org': 0.8,
            'docs.microsoft.com': 0.8,
            'docs.oracle.com': 0.8,
            'pkg.go.dev': 0.8,
            'docs.rs': 0.8,
            'hexdocs.pm': 0.8,
            'rubydoc.info': 0.8,
            'godoc.org': 0.8,
        }

        self.package_managers = {
            'python': ['pip', 'conda', 'poetry'],
            'javascript': ['npm', 'yarn', 'pnpm'],
            'java': ['maven', 'gradle'],
            'ruby': ['gem', 'bundler'],
            'php': ['composer'],
            'rust': ['cargo'],
            'go': ['go get'],
        }

    async def discover_doc_url(self, package_name: str) -> Optional[str]:
        """Dynamically discover documentation URL for a package."""
        try:
            # Try PyPI API first
            async with aiohttp.ClientSession() as session:
                pypi_url = f"https://pypi.org/pypi/{package_name}/json"
                async with session.get(pypi_url) as response:
                    if response.status == 200:
                        data = await response.json()
                        if 'info' in data:
                            # Check various documentation fields
                            for field in ['documentation_url', 'project_urls', 'home_page']:
                                if field in data['info'] and data['info'][field]:
                                    if field == 'project_urls':
                                        # Look for documentation-related URLs
                                        for key, url in data['info'][field].items():
                                            if any(doc_term in key.lower() for doc_term in ['doc', 'wiki', 'guide']):
                                                return url
                                    else:
                                        return data['info'][field]

            # Try common documentation patterns
            for pattern in self.doc_patterns:
                url = pattern.format(package=package_name.lower())
                try:
                    # Use a new session for each pattern check or reuse one if performance is critical
                    async with aiohttp.ClientSession() as session:
                        async with session.head(url, allow_redirects=True) as response:
                            if response.status == 200:
                                return url
                except aiohttp.ClientError as client_err: # Catch specific client errors
                    logging.debug(f"Client error checking pattern {url}: {client_err}")
                    continue
                except Exception as e: # Catch other potential errors (timeouts, etc.)
                    logging.debug(f"Error checking pattern {url}: {e}")
                    continue # Continue to the next pattern

            return None

        except Exception as e:
            logging.error(f"Error discovering documentation URL for {package_name}: {str(e)}")
            return None

    def add_doc_url(self, package_name: str, url: str) -> None:
        """Add or update a package documentation URL."""
        self.package_doc_urls[package_name] = url

    def add_fallback_url(self, package_name: str, url: str) -> None:
        """Add or update a fallback URL for a package."""
        self.fallback_urls[package_name] = url

    async def identify_from_url(self, url: str) -> ProjectIdentity:
        """Identify project type from a URL."""
        confidence = 0.0
        project_type = ProjectType.UNKNOWN
        language = None
        framework = None

        # Check if it's a known documentation platform
        for platform, conf in self.doc_platforms.items():
            if platform in url:
                confidence = max(confidence, conf)
                break

        # Extract potential project name from URL
        name = self._extract_name_from_url(url)

        # Identify language from URL patterns
        for lang, patterns in self.language_patterns.items():
            if any(re.search(pattern, url, re.I) for pattern in patterns):
                language = lang
                confidence = max(confidence, 0.7)
                break

        # Identify framework from URL patterns
        for fw, patterns in self.framework_patterns.items():
            if any(re.search(pattern, url, re.I) for pattern in patterns):
                framework = fw
                project_type = ProjectType.FRAMEWORK
                confidence = max(confidence, 0.8)
                break

        return ProjectIdentity(
            name=name,
            type=project_type,
            language=language,
            framework=framework,
            confidence=confidence
        )

    async def identify_from_content(self, content: str) -> ProjectIdentity:
        """Identify project type from content."""
        # Initialize counters for different project types
        type_scores = {
            ProjectType.PACKAGE: 0,
            ProjectType.FRAMEWORK: 0,
            ProjectType.PROGRAM: 0,
            ProjectType.LIBRARY: 0,
            ProjectType.CLI_TOOL: 0,
            ProjectType.WEB_APP: 0,
            ProjectType.API: 0,
        }

        # Keywords associated with different project types
        type_keywords = {
            ProjectType.PACKAGE: ['import', 'require', 'dependency', 'module'],
            ProjectType.FRAMEWORK: ['framework', 'middleware', 'plugin', 'extension'],
            ProjectType.PROGRAM: ['executable', 'binary', 'command-line', 'CLI'],
            ProjectType.LIBRARY: ['library', 'SDK', 'toolkit', 'API'],
            ProjectType.CLI_TOOL: ['command', 'terminal', 'shell', 'console'],
            ProjectType.WEB_APP: ['webapp', 'website', 'frontend', 'backend'],
            ProjectType.API: ['API', 'REST', 'GraphQL', 'endpoint'],
        }

        # Score content based on keywords
        for project_type, keywords in type_keywords.items():
            score = sum(1 for keyword in keywords if re.search(rf'\b{keyword}\b', content, re.I))
            type_scores[project_type] = score

        # Get the project type with highest score
        project_type = max(type_scores.items(), key=lambda x: x[1])[0]
        if type_scores[project_type] == 0:
            project_type = ProjectType.UNKNOWN

        # Extract potential name from content
        name = self._extract_name_from_content(content)

        # Calculate confidence based on keyword matches
        max_score = max(type_scores.values())
        total_matches = sum(type_scores.values())
        confidence = max_score / (total_matches + 1) if total_matches > 0 else 0.0

        return ProjectIdentity(
            name=name,
            type=project_type,
            confidence=confidence
        )

    def _extract_name_from_url(self, url: str) -> str:
        """Extract potential project name from URL."""
        # Remove common prefixes and suffixes
        url = re.sub(r'^https?://(www\.)?', '', url)
        url = re.sub(r'\.html?$', '', url)

        # Try to extract name from common documentation URLs
        doc_patterns = [
            r'([^/]+)\.readthedocs\.org',
            r'docs\.([^/]+)\.org',
            r'/([^/]+)/docs?/',
            r'/projects?/([^/]+)',
            r'/packages?/([^/]+)',
        ]

        for pattern in doc_patterns:
            match = re.search(pattern, url, re.I)
            if match:
                return match.group(1)

        # Fall back to last meaningful URL segment
        segments = [s for s in url.split('/') if s and not s.startswith('?')]
        return segments[-1] if segments else "unknown"

    def _extract_name_from_content(self, content: str) -> str:
        """Extract potential project name from content."""
        # Look for common project name indicators
        patterns = [
            r'<title>([^<]+)</title>',
            r'# ([^\n]+)',
            r'== ([^=]+) ==',
            r'project["\']\s*:\s*["\']([^"\']+)',
            r'name["\']\s*:\s*["\']([^"\']+)',
        ]

        for pattern in patterns:
            match = re.search(pattern, content)
            if match:
                name = match.group(1).strip()
                # Clean up common suffixes
                name = re.sub(r'\s*(-|–|—)\s*(documentation|docs|manual|guide)$', '', name, flags=re.I)
                return name

        return "unknown"

# --- End of copied code ---