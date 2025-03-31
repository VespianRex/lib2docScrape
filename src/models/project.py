from enum import Enum
from typing import List, Optional
from dataclasses import dataclass


class ProjectType(Enum):
    """Enumeration of project types."""
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
    """Class representing project identity information."""
    name: str
    type: ProjectType
    language: Optional[str] = None
    framework: Optional[str] = None
    repository: Optional[str] = None
    package_manager: Optional[str] = None
    main_doc_url: Optional[str] = None
    related_keywords: List[str] = None
    confidence: float = 0.0

    def __post_init__(self):
        if self.related_keywords is None:
            self.related_keywords = []


class ProjectIdentifier:
    """Class for identifying project type and characteristics."""

    def _detect_language(self, files: List[str]) -> Optional[str]:
        """Detect programming language based on file extensions and names."""
        extensions = {
            ".py": "python",
            ".js": "javascript",
            ".ts": "typescript",
            ".java": "java",
            ".rb": "ruby",
            ".php": "php",
            ".go": "go",
            ".rs": "rust",
            ".cs": "csharp",
            ".cpp": "c++",
            ".c": "c"
        }

        language_indicators = {
            "python": ["requirements.txt", "setup.py", "pyproject.toml", "Pipfile"],
            "javascript": ["package.json", "yarn.lock", "webpack.config.js"],
            "typescript": ["tsconfig.json", "tslint.json"],
            "ruby": ["Gemfile", "Rakefile"],
            "php": ["composer.json", "artisan"],
            "java": ["pom.xml", "build.gradle", "gradlew"],
            "go": ["go.mod", "go.sum"],
            "rust": ["Cargo.toml", "Cargo.lock"]
        }

        # Count occurrences of each language
        lang_counts = {}

        for file in files:
            # Check file extensions
            for ext, lang in extensions.items():
                if file.lower().endswith(ext):
                    lang_counts[lang] = lang_counts.get(lang, 0) + 1

            # Check language indicators
            for lang, indicators in language_indicators.items():
                if any(ind.lower() in file.lower() for ind in indicators):
                    lang_counts[lang] = lang_counts.get(lang, 0) + 5  # Give more weight to indicators

        if not lang_counts:
            return None

        # Return the language with the highest count
        return max(lang_counts.items(), key=lambda x: x[1])[0]

    def _detect_framework(self, files: List[str], language: Optional[str]) -> Optional[str]:
        """Detect framework based on file patterns and language."""
        framework_indicators = {
            "python": {
                "django": ["manage.py", "wsgi.py", "asgi.py", "settings.py"],
                "flask": ["app.py", "wsgi.py", "requirements.txt"],
                "fastapi": ["main.py", "app.py", "api.py"],
                "pyramid": ["development.ini", "production.ini"],
            },
            "javascript": {
                "react": ["react", "jsx", "tsx"],
                "vue": ["vue.config.js", ".vue"],
                "angular": ["angular.json", ".component.ts"],
                "next": ["next.config.js"],
            },
            "ruby": {
                "rails": ["config/routes.rb", "app/controllers"],
                "sinatra": ["config.ru"],
            },
            "php": {
                "laravel": ["artisan", "composer.json"],
                "symfony": ["symfony.lock", "composer.json"],
            }
        }

        if not language or language not in framework_indicators:
            return None

        framework_counts = {}
        for framework, patterns in framework_indicators[language].items():
            for pattern in patterns:
                if any(pattern.lower() in file.lower() for file in files):
                    framework_counts[framework] = framework_counts.get(framework, 0) + 1

        if not framework_counts:
            return None

        return max(framework_counts.items(), key=lambda x: x[1])[0]

    def _generate_doc_urls(self, identity: ProjectIdentity) -> List[str]:
        """Generate potential documentation URLs based on project identity."""
        urls = []
        name = identity.name.lower().replace(" ", "-")

        # Common documentation patterns
        patterns = [
            f"https://{name}.readthedocs.io/en/latest/",
            f"https://docs.{name}.org/",
            f"https://{name}.dev/docs/",
            f"https://{name}.io/docs/",
        ]

        # Add GitHub/GitLab pages if repository is available
        if identity.repository:
            if "github.com" in identity.repository:
                urls.append(f"{identity.repository}/wiki")
                urls.append(f"https://{name}.github.io/")
            elif "gitlab.com" in identity.repository:
                urls.append(f"{identity.repository}/-/wikis/home")
                urls.append(f"https://{name}.gitlab.io/")

        urls.extend(patterns)
        return urls