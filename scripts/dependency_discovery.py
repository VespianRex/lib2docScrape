#!/usr/bin/env python3
"""
Dependency Discovery Tool for lib2docScrape

This tool analyzes a project folder to automatically discover all dependencies by:
1. Parsing package configuration files (pyproject.toml, requirements.txt, etc.)
2. Scanning source code for import statements
3. Analyzing installed packages in virtual environments
4. Cross-referencing with PyPI to get documentation URLs

Usage:
    python scripts/dependency_discovery.py [project_path]
    python scripts/dependency_discovery.py --scan-imports src/
    python scripts/dependency_discovery.py --output deps.json
"""

import argparse
import ast
import json
import logging
import re
import subprocess
import sys
from pathlib import Path

try:
    import toml
except ImportError:
    toml = None

try:
    import requests
except ImportError:
    requests = None

logger = logging.getLogger(__name__)


class DependencyDiscovery:
    """Discovers project dependencies from multiple sources."""

    def __init__(self, project_path: str = "."):
        self.project_path = Path(project_path).resolve()
        self.dependencies = {
            "config_files": {},  # From pyproject.toml, requirements.txt, etc.
            "imports": {},  # From import statements in code
            "installed": {},  # From pip list/uv pip list
            "documentation_urls": {},  # Discovered documentation URLs
        }

        # Common package file patterns
        self.package_files = [
            "pyproject.toml",
            "requirements.txt",
            "requirements-dev.txt",
            "requirements/*.txt",
            "setup.py",
            "setup.cfg",
            "Pipfile",
            "poetry.lock",
            "package.json",  # For Node.js projects
            "Cargo.toml",  # For Rust projects
            "go.mod",  # For Go projects
        ]

        # Standard library modules to exclude
        self.stdlib_modules = {
            "os",
            "sys",
            "json",
            "logging",
            "pathlib",
            "typing",
            "datetime",
            "asyncio",
            "time",
            "collections",
            "re",
            "subprocess",
            "argparse",
            "functools",
            "itertools",
            "math",
            "random",
            "string",
            "urllib",
            "http",
            "email",
            "xml",
            "html",
            "csv",
            "sqlite3",
            "threading",
            "multiprocessing",
            "concurrent",
            "queue",
            "socket",
            "ssl",
            "hashlib",
            "hmac",
            "base64",
            "binascii",
            "struct",
            "array",
            "weakref",
            "copy",
            "pickle",
            "shelve",
            "dbm",
            "zlib",
            "gzip",
            "bz2",
            "lzma",
            "zipfile",
            "tarfile",
            "tempfile",
            "shutil",
            "glob",
            "fnmatch",
            "linecache",
            "fileinput",
            "stat",
            "filecmp",
            "unittest",
            "doctest",
            "pdb",
            "profile",
            "pstats",
            "timeit",
            "trace",
            "gc",
            "inspect",
            "site",
            "importlib",
            "pkgutil",
            "modulefinder",
            "runpy",
            "warnings",
            "contextlib",
            "abc",
            "atexit",
            "traceback",
            "future",
            "__future__",
            "builtins",
        }

    def discover_from_config_files(self) -> dict[str, list[str]]:
        """Discover dependencies from configuration files."""
        config_deps = {}

        # Check pyproject.toml
        pyproject_file = self.project_path / "pyproject.toml"
        if pyproject_file.exists() and toml:
            config_deps.update(self._parse_pyproject_toml(pyproject_file))

        # Check requirements files
        for req_pattern in ["requirements*.txt", "requirements/*.txt"]:
            for req_file in self.project_path.glob(req_pattern):
                deps = self._parse_requirements_txt(req_file)
                config_deps[f"requirements_{req_file.name}"] = deps

        # Check setup.py
        setup_file = self.project_path / "setup.py"
        if setup_file.exists():
            deps = self._parse_setup_py(setup_file)
            if deps:
                config_deps["setup_py"] = deps

        # Check package.json (for projects with Node.js components)
        package_json = self.project_path / "package.json"
        if package_json.exists():
            deps = self._parse_package_json(package_json)
            if deps:
                config_deps["package_json"] = deps

        self.dependencies["config_files"] = config_deps
        return config_deps

    def discover_from_imports(
        self, source_dirs: list[str] = None
    ) -> dict[str, set[str]]:
        """Discover dependencies by scanning import statements in source code."""
        if source_dirs is None:
            source_dirs = ["src", "lib", ".", "tests"]

        imports_by_file = {}
        all_imports = set()

        for source_dir in source_dirs:
            source_path = self.project_path / source_dir
            if not source_path.exists():
                continue

            logger.info(f"Scanning imports in {source_path}")

            # Find all Python files
            python_files = list(source_path.rglob("*.py"))

            for py_file in python_files:
                try:
                    file_imports = self._extract_imports_from_file(py_file)
                    if file_imports:
                        rel_path = py_file.relative_to(self.project_path)
                        imports_by_file[str(rel_path)] = file_imports
                        all_imports.update(file_imports)
                except Exception as e:
                    logger.warning(f"Failed to parse {py_file}: {e}")

        # Filter out standard library modules and local imports
        external_imports = self._filter_external_imports(all_imports)

        self.dependencies["imports"] = {
            "by_file": {k: list(v) for k, v in imports_by_file.items()},
            "all_external": list(external_imports),
            "all_raw": list(all_imports),
        }

        return self.dependencies["imports"]

    def discover_installed_packages(self) -> list[str]:
        """Discover installed packages in the current environment."""
        installed = []

        # Try uv pip list first
        try:
            result = subprocess.run(
                ["uv", "pip", "list", "--format=json"],
                capture_output=True,
                text=True,
                check=True,
            )
            packages = json.loads(result.stdout)
            installed = [pkg["name"] for pkg in packages]
            logger.info(f"Found {len(installed)} packages via 'uv pip list'")
        except (subprocess.CalledProcessError, FileNotFoundError, json.JSONDecodeError):
            # Fallback to regular pip
            try:
                result = subprocess.run(
                    ["pip", "list", "--format=json"],
                    capture_output=True,
                    text=True,
                    check=True,
                )
                packages = json.loads(result.stdout)
                installed = [pkg["name"] for pkg in packages]
                logger.info(f"Found {len(installed)} packages via 'pip list'")
            except Exception as e:
                logger.warning(f"Failed to get installed packages: {e}")

        self.dependencies["installed"] = installed
        return installed

    def discover_documentation_urls(self, packages: list[str]) -> dict[str, str]:
        """Discover documentation URLs for packages."""
        doc_urls = {}

        # Predefined documentation patterns for common packages
        known_patterns = {
            "requests": "https://requests.readthedocs.io/en/latest/",
            "aiohttp": "https://docs.aiohttp.org/en/stable/",
            "fastapi": "https://fastapi.tiangolo.com/",
            "django": "https://docs.djangoproject.com/",
            "flask": "https://flask.palletsprojects.com/",
            "pytest": "https://docs.pytest.org/en/stable/",
            "numpy": "https://numpy.org/doc/stable/",
            "pandas": "https://pandas.pydata.org/docs/",
            "matplotlib": "https://matplotlib.org/stable/",
            "scikit-learn": "https://scikit-learn.org/stable/",
            "tensorflow": "https://www.tensorflow.org/api_docs/python/",
            "torch": "https://pytorch.org/docs/stable/",
            "pydantic": "https://docs.pydantic.dev/latest/",
            "sqlalchemy": "https://docs.sqlalchemy.org/",
            "celery": "https://docs.celeryproject.org/",
            "redis": "https://redis-py.readthedocs.io/",
            "beautifulsoup4": "https://www.crummy.com/software/BeautifulSoup/bs4/doc/",
            "scrapy": "https://docs.scrapy.org/en/latest/",
            "selenium": "https://selenium-python.readthedocs.io/",
            "pillow": "https://pillow.readthedocs.io/",
            "click": "https://click.palletsprojects.com/",
            "jinja2": "https://jinja.palletsprojects.com/",
            "markdownify": "https://pypi.org/project/markdownify/",
            "bleach": "https://bleach.readthedocs.io/en/latest/",
            "tldextract": "https://github.com/john-kurkowski/tldextract",
            "psutil": "https://psutil.readthedocs.io/en/latest/",
            "httpx": "https://www.python-httpx.org/",
            "uvloop": "https://github.com/MagicStack/uvloop",
            "ruff": "https://docs.astral.sh/ruff/",
            "coverage": "https://coverage.readthedocs.io/en/latest/",
        }

        for package in packages:
            package_lower = package.lower().replace("-", "").replace("_", "")

            # Check known patterns first
            if package_lower in known_patterns:
                doc_urls[package] = known_patterns[package_lower]
                continue

            # Try common documentation URL patterns
            common_patterns = [
                f"https://{package_lower}.readthedocs.io/en/latest/",
                f"https://docs.{package_lower}.org/",
                f"https://{package_lower}.org/docs/",
                f"https://{package_lower}.org/documentation/",
                f"https://pypi.org/project/{package}/",
            ]

            # For now, use the first pattern (ReadTheDocs is most common)
            # In a more sophisticated version, we could check which URLs actually exist
            doc_urls[package] = common_patterns[0]

        self.dependencies["documentation_urls"] = doc_urls
        return doc_urls

    def _parse_pyproject_toml(self, file_path: Path) -> dict[str, list[str]]:
        """Parse dependencies from pyproject.toml."""
        try:
            with open(file_path) as f:
                data = toml.load(f)

            deps = {}

            # Main dependencies
            if "project" in data and "dependencies" in data["project"]:
                main_deps = []
                for dep in data["project"]["dependencies"]:
                    pkg_name = re.split(r"[>=<!=\[\]]", dep)[0].strip()
                    main_deps.append(pkg_name)
                deps["main"] = main_deps

            # Optional dependencies
            if "project" in data and "optional-dependencies" in data["project"]:
                for group, group_deps in data["project"][
                    "optional-dependencies"
                ].items():
                    parsed_deps = []
                    for dep in group_deps:
                        pkg_name = re.split(r"[>=<!=\[\]]", dep)[0].strip()
                        parsed_deps.append(pkg_name)
                    deps[f"optional_{group}"] = parsed_deps

            return deps

        except Exception as e:
            logger.warning(f"Failed to parse {file_path}: {e}")
            return {}

    def _parse_requirements_txt(self, file_path: Path) -> list[str]:
        """Parse dependencies from requirements.txt."""
        try:
            with open(file_path) as f:
                lines = f.readlines()

            deps = []
            for line in lines:
                line = line.strip()
                if line and not line.startswith("#") and not line.startswith("-"):
                    # Extract package name (remove version constraints)
                    pkg_name = re.split(r"[>=<!=\[\]]", line)[0].strip()
                    if pkg_name:
                        deps.append(pkg_name)

            return deps

        except Exception as e:
            logger.warning(f"Failed to parse {file_path}: {e}")
            return []

    def _parse_setup_py(self, file_path: Path) -> list[str]:
        """Parse dependencies from setup.py (basic extraction)."""
        try:
            with open(file_path) as f:
                content = f.read()

            # Look for install_requires or requires patterns
            deps = []

            # Simple regex patterns for common setup.py formats
            patterns = [
                r"install_requires\s*=\s*\[(.*?)\]",
                r"requires\s*=\s*\[(.*?)\]",
                r"dependencies\s*=\s*\[(.*?)\]",
            ]

            for pattern in patterns:
                matches = re.findall(pattern, content, re.DOTALL)
                for match in matches:
                    # Extract quoted strings
                    quoted_deps = re.findall(r'["\']([^"\']+)["\']', match)
                    for dep in quoted_deps:
                        pkg_name = re.split(r"[>=<!=\[\]]", dep)[0].strip()
                        if pkg_name:
                            deps.append(pkg_name)

            return deps

        except Exception as e:
            logger.warning(f"Failed to parse {file_path}: {e}")
            return []

    def _parse_package_json(self, file_path: Path) -> list[str]:
        """Parse dependencies from package.json (for Node.js components)."""
        try:
            with open(file_path) as f:
                data = json.load(f)

            deps = []
            for dep_type in ["dependencies", "devDependencies"]:
                if dep_type in data:
                    deps.extend(data[dep_type].keys())

            return deps

        except Exception as e:
            logger.warning(f"Failed to parse {file_path}: {e}")
            return []

    def _extract_imports_from_file(self, file_path: Path) -> set[str]:
        """Extract import statements from a Python file."""
        imports = set()

        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Parse the AST
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.add(alias.name.split(".")[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.add(node.module.split(".")[0])

        except Exception as e:
            logger.debug(f"Failed to parse AST for {file_path}: {e}")
            # Fallback to regex parsing
            try:
                with open(file_path, encoding="utf-8") as f:
                    content = f.read()

                # Simple regex patterns for imports
                import_patterns = [
                    r"^import\s+([a-zA-Z_][a-zA-Z0-9_]*)",
                    r"^from\s+([a-zA-Z_][a-zA-Z0-9_]*)\s+import",
                ]

                for pattern in import_patterns:
                    matches = re.findall(pattern, content, re.MULTILINE)
                    imports.update(matches)

            except Exception as e2:
                logger.warning(f"Failed to extract imports from {file_path}: {e2}")

        return imports

    def _filter_external_imports(self, imports: set[str]) -> set[str]:
        """Filter out standard library and local imports."""
        external = set()

        for imp in imports:
            # Skip standard library modules
            if imp in self.stdlib_modules:
                continue

            # Skip relative imports and local modules
            if imp.startswith(".") or imp in ["src", "tests", "scripts"]:
                continue

            # Skip common local patterns
            if any(pattern in imp.lower() for pattern in ["test", "mock", "fixture"]):
                continue

            external.add(imp)

        return external

    def get_all_dependencies(self) -> set[str]:
        """Get all unique dependencies from all sources."""
        all_deps = set()

        # From config files
        for _source, deps in self.dependencies["config_files"].items():
            if isinstance(deps, list):
                all_deps.update(deps)
            elif isinstance(deps, dict):
                for group_deps in deps.values():
                    if isinstance(group_deps, list):
                        all_deps.update(group_deps)

        # From imports
        if "all_external" in self.dependencies["imports"]:
            all_deps.update(self.dependencies["imports"]["all_external"])

        # From installed packages (optional, might be too many)
        # all_deps.update(self.dependencies["installed"])

        return all_deps

    def generate_report(self) -> dict:
        """Generate a comprehensive dependency report."""
        all_deps = self.get_all_dependencies()

        return {
            "project_path": str(self.project_path),
            "discovery_timestamp": str(Path().cwd()),
            "summary": {
                "total_unique_dependencies": len(all_deps),
                "config_file_sources": len(self.dependencies["config_files"]),
                "python_files_scanned": len(
                    self.dependencies["imports"].get("by_file", {})
                ),
                "installed_packages": len(self.dependencies["installed"]),
            },
            "dependencies": {
                "all_unique": sorted(all_deps),
                "by_source": self.dependencies,
            },
        }

    def save_report(self, output_file: str):
        """Save the dependency report to a file."""
        report = self.generate_report()

        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(report, f, indent=2, default=str)

        logger.info(f"Dependency report saved to {output_path}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Discover project dependencies")

    parser.add_argument(
        "project_path",
        nargs="?",
        default=".",
        help="Path to project directory (default: current directory)",
    )
    parser.add_argument(
        "--scan-imports",
        nargs="+",
        default=["src", "lib", "tests"],
        help="Directories to scan for imports",
    )
    parser.add_argument(
        "--output",
        "-o",
        default="reports/dependencies.json",
        help="Output file for dependency report",
    )
    parser.add_argument(
        "--include-installed",
        action="store_true",
        help="Include all installed packages in environment",
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    # Create discovery tool
    discovery = DependencyDiscovery(args.project_path)

    try:
        logger.info(f"Discovering dependencies in {discovery.project_path}")

        # Discover from all sources
        config_deps = discovery.discover_from_config_files()
        import_deps = discovery.discover_from_imports(args.scan_imports)

        if args.include_installed:
            discovery.discover_installed_packages()

        # Get all unique dependencies
        all_deps = discovery.get_all_dependencies()

        # Discover documentation URLs
        discovery.discover_documentation_urls(list(all_deps))

        # Generate and save report
        discovery.save_report(args.output)

        # Print summary
        print("\n" + "=" * 60)
        print("DEPENDENCY DISCOVERY SUMMARY")
        print("=" * 60)
        print(f"Project: {discovery.project_path}")
        print(f"Total unique dependencies: {len(all_deps)}")
        print(f"Config file sources: {len(config_deps)}")
        print(f"Python files scanned: {len(import_deps.get('by_file', {}))}")

        if all_deps:
            print("\nTop dependencies found:")
            for dep in sorted(all_deps)[:10]:
                print(f"  - {dep}")
            if len(all_deps) > 10:
                print(f"  ... and {len(all_deps) - 10} more")

        print(f"\nReport saved to: {args.output}")
        print("=" * 60)

        return 0

    except Exception as e:
        logger.error(f"Dependency discovery failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
