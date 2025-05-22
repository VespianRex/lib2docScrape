"""Tests for the project models."""

import pytest
from src.models.project import ProjectType, ProjectIdentity, ProjectIdentifier


class TestProjectType:
    """Tests for the ProjectType enum."""

    def test_enum_values(self):
        """Test that enum values are correct."""
        assert ProjectType.PACKAGE.value == "package"
        assert ProjectType.FRAMEWORK.value == "framework"
        assert ProjectType.PROGRAM.value == "program"
        assert ProjectType.LIBRARY.value == "library"
        assert ProjectType.CLI_TOOL.value == "cli_tool"
        assert ProjectType.WEB_APP.value == "web_app"
        assert ProjectType.API.value == "api"
        assert ProjectType.UNKNOWN.value == "unknown"


class TestProjectIdentity:
    """Tests for the ProjectIdentity class."""

    def test_init_minimal(self):
        """Test initialization with minimal parameters."""
        identity = ProjectIdentity(
            name="test-project",
            type=ProjectType.LIBRARY
        )
        assert identity.name == "test-project"
        assert identity.type == ProjectType.LIBRARY
        assert identity.language is None
        assert identity.framework is None
        assert identity.repository is None
        assert identity.package_manager is None
        assert identity.main_doc_url is None
        assert identity.related_keywords == []
        assert identity.confidence == 0.0

    def test_init_full(self):
        """Test initialization with all parameters."""
        identity = ProjectIdentity(
            name="test-project",
            type=ProjectType.LIBRARY,
            language="python",
            framework="flask",
            repository="https://github.com/test/test-project",
            package_manager="pip",
            main_doc_url="https://test-project.readthedocs.io",
            related_keywords=["web", "api"],
            confidence=0.85
        )
        assert identity.name == "test-project"
        assert identity.type == ProjectType.LIBRARY
        assert identity.language == "python"
        assert identity.framework == "flask"
        assert identity.repository == "https://github.com/test/test-project"
        assert identity.package_manager == "pip"
        assert identity.main_doc_url == "https://test-project.readthedocs.io"
        assert identity.related_keywords == ["web", "api"]
        assert identity.confidence == 0.85

    def test_post_init_related_keywords(self):
        """Test that related_keywords is initialized as an empty list if None."""
        identity = ProjectIdentity(
            name="test-project",
            type=ProjectType.LIBRARY,
            related_keywords=None
        )
        assert identity.related_keywords == []


class TestProjectIdentifier:
    """Tests for the ProjectIdentifier class."""

    def test_detect_language_python(self):
        """Test detecting Python language."""
        identifier = ProjectIdentifier()
        files = [
            "setup.py",
            "requirements.txt",
            "src/main.py",
            "tests/test_main.py"
        ]
        assert identifier._detect_language(files) == "python"

    def test_detect_language_javascript(self):
        """Test detecting JavaScript language."""
        identifier = ProjectIdentifier()
        files = [
            "package.json",
            "webpack.config.js",
            "src/index.js",
            "tests/test.js"
        ]
        assert identifier._detect_language(files) == "javascript"

    def test_detect_language_typescript(self):
        """Test detecting TypeScript language."""
        identifier = ProjectIdentifier()
        files = [
            "tsconfig.json",
            "src/index.ts",
            "tests/test.ts"
        ]
        assert identifier._detect_language(files) == "typescript"

    def test_detect_language_ruby(self):
        """Test detecting Ruby language."""
        identifier = ProjectIdentifier()
        files = [
            "Gemfile",
            "Rakefile",
            "app/models/user.rb"
        ]
        assert identifier._detect_language(files) == "ruby"

    def test_detect_language_php(self):
        """Test detecting PHP language."""
        identifier = ProjectIdentifier()
        files = [
            "composer.json",
            "artisan",
            "app/Http/Controllers/UserController.php"
        ]
        assert identifier._detect_language(files) == "php"

    def test_detect_language_java(self):
        """Test detecting Java language."""
        identifier = ProjectIdentifier()
        files = [
            "pom.xml",
            "src/main/java/com/example/Main.java",
            "src/test/java/com/example/MainTest.java"
        ]
        assert identifier._detect_language(files) == "java"

    def test_detect_language_go(self):
        """Test detecting Go language."""
        identifier = ProjectIdentifier()
        files = [
            "go.mod",
            "go.sum",
            "main.go",
            "pkg/service/service.go"
        ]
        assert identifier._detect_language(files) == "go"

    def test_detect_language_rust(self):
        """Test detecting Rust language."""
        identifier = ProjectIdentifier()
        files = [
            "Cargo.toml",
            "Cargo.lock",
            "src/main.rs",
            "tests/test.rs"
        ]
        assert identifier._detect_language(files) == "rust"

    def test_detect_language_mixed(self):
        """Test detecting language with mixed file types."""
        identifier = ProjectIdentifier()
        files = [
            "setup.py",  # Python
            "requirements.txt",  # Python
            "package.json",  # JavaScript
            "src/main.py",  # Python
            "src/index.js",  # JavaScript
            "tests/test.py"  # Python
        ]
        # Python should win due to more indicators
        assert identifier._detect_language(files) == "python"

    def test_detect_language_none(self):
        """Test detecting language with no recognizable files."""
        identifier = ProjectIdentifier()
        files = [
            "README.md",
            "LICENSE",
            "docs/index.html"
        ]
        assert identifier._detect_language(files) is None

    def test_detect_framework_django(self):
        """Test detecting Django framework."""
        identifier = ProjectIdentifier()
        files = [
            "manage.py",
            "wsgi.py",
            "settings.py",
            "urls.py"
        ]
        assert identifier._detect_framework(files, "python") == "django"

    def test_detect_framework_flask(self):
        """Test detecting Flask framework."""
        identifier = ProjectIdentifier()
        files = [
            "app.py",
            "wsgi.py",
            "requirements.txt"
        ]
        assert identifier._detect_framework(files, "python") == "flask"

    def test_detect_framework_react(self):
        """Test detecting React framework."""
        identifier = ProjectIdentifier()
        files = [
            "package.json",
            "src/App.jsx",
            "public/index.html"
        ]
        assert identifier._detect_framework(files, "javascript") == "react"

    def test_detect_framework_rails(self):
        """Test detecting Rails framework."""
        identifier = ProjectIdentifier()
        files = [
            "config/routes.rb",
            "app/controllers/users_controller.rb",
            "Gemfile"
        ]
        assert identifier._detect_framework(files, "ruby") == "rails"

    def test_detect_framework_laravel(self):
        """Test detecting Laravel framework."""
        identifier = ProjectIdentifier()
        files = [
            "artisan",
            "composer.json",
            "app/Http/Controllers/Controller.php"
        ]
        assert identifier._detect_framework(files, "php") == "laravel"

    def test_detect_framework_unknown_language(self):
        """Test detecting framework with unknown language."""
        identifier = ProjectIdentifier()
        files = [
            "manage.py",
            "wsgi.py",
            "settings.py"
        ]
        assert identifier._detect_framework(files, "unknown") is None

    def test_detect_framework_none(self):
        """Test detecting framework with no recognizable files."""
        identifier = ProjectIdentifier()
        files = [
            "custom.py",
            "utils.py",
            "README.md"
        ]
        # Note: main.py is detected as FastAPI, so we use custom.py instead
        assert identifier._detect_framework(files, "python") is None

    def test_generate_doc_urls_basic(self):
        """Test generating documentation URLs with basic identity."""
        identifier = ProjectIdentifier()
        identity = ProjectIdentity(
            name="test-project",
            type=ProjectType.LIBRARY
        )
        urls = identifier._generate_doc_urls(identity)
        assert "https://test-project.readthedocs.io/en/latest/" in urls
        assert "https://docs.test-project.org/" in urls
        assert "https://test-project.dev/docs/" in urls
        assert "https://test-project.io/docs/" in urls

    def test_generate_doc_urls_github(self):
        """Test generating documentation URLs with GitHub repository."""
        identifier = ProjectIdentifier()
        identity = ProjectIdentity(
            name="test-project",
            type=ProjectType.LIBRARY,
            repository="https://github.com/test/test-project"
        )
        urls = identifier._generate_doc_urls(identity)
        assert "https://github.com/test/test-project/wiki" in urls
        assert "https://test-project.github.io/" in urls

    def test_generate_doc_urls_gitlab(self):
        """Test generating documentation URLs with GitLab repository."""
        identifier = ProjectIdentifier()
        identity = ProjectIdentity(
            name="test-project",
            type=ProjectType.LIBRARY,
            repository="https://gitlab.com/test/test-project"
        )
        urls = identifier._generate_doc_urls(identity)
        assert "https://gitlab.com/test/test-project/-/wikis/home" in urls
        assert "https://test-project.gitlab.io/" in urls
