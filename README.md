# lib2docScrape

A comprehensive web scraping tool for library documentation with multiple backend support. Designed to efficiently crawl, process, and organize technical documentation from various sources with intelligent content extraction and quality assurance.

## Features

### 🚀 **Multi-Backend Architecture**
- **Crawl4AI**: Advanced AI-powered crawling with JavaScript rendering
- **Playwright**: High-performance browser automation for modern web apps
- **Lightpanda**: Lightweight browser engine for efficient scraping
- **Scrapy**: High-throughput crawling for large-scale operations
- **HTTP Backend**: Simple HTTP requests for basic content
- **File Backend**: Local file system processing

### 📄 **Content Processing**
- **Smart Structure Detection**: Automatic identification of documentation sections
- **Format Support**: HTML, Markdown, reStructuredText, and more
- **Code Extraction**: Syntax highlighting and code block preservation
- **Metadata Extraction**: Automatic title, description, and tag detection
- **Asset Handling**: Images, PDFs, and other media files

### 🔍 **Quality Assurance**
- **Content Validation**: Automated quality checks and scoring
- **Link Verification**: Broken link detection and reporting
- **Duplicate Detection**: Content deduplication and similarity analysis
- **Metadata Verification**: Required field validation

### 🎯 **Advanced URL Handling**
- **Intelligent Classification**: Automatic URL type detection
- **Security Validation**: Path traversal and malicious URL detection
- **Normalization**: RFC-compliant URL standardization
- **Domain Analysis**: TLD extraction and subdomain classification

## Installation

### Prerequisites
- Python 3.9 or higher
- uv (recommended) or pip for package management

### Using uv (Recommended)
```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Clone the repository
git clone https://github.com/VespianRex/lib2docscrape.git
cd lib2docscrape

# Install with development dependencies
uv sync --extra dev

# Or install specific backend extras
uv sync --extra crawl4ai --extra playwright
```

### Using pip
```bash
pip install -e .[dev]  # Development installation
pip install -e .[all]  # All optional dependencies
```

## Quick Start

### Development Setup
```bash
# Run tests to verify installation
uv run pytest

# Start the web interface
uv run python src/main.py

# Run with specific backend
uv run python -m src.main --backend crawl4ai
```

### Basic Usage
```python
from src.crawler import DocumentationCrawler
from src.crawler.models import CrawlTarget, CrawlerConfig

# Create crawler configuration
config = CrawlerConfig(
    concurrent_requests=5,
    requests_per_second=2.0,
    max_retries=3
)

# Define crawl target
target = CrawlTarget(
    url="https://docs.example.com",
    depth=2,
    follow_external=False
)

# Initialize and run crawler
crawler = DocumentationCrawler(config)
result = await crawler.crawl(target)

print(f"Crawled {len(result.pages)} pages")
```

### Web Interface

1. Start the server: `uv run python src/main.py`
2. Access the web interface at `http://localhost:8000`
3. Use the dashboard to:
   - Configure scraping targets
   - Monitor scraping progress
   - View and organize documentation
   - Export documentation

## Supported Documentation Types

- API Documentation
  - OpenAPI/Swagger
  - API Blueprint
  - GraphQL schemas

- Technical Documentation
  - Product documentation
  - User guides
  - Developer guides
  - Reference documentation

- Knowledge Bases
  - Wiki pages
  - Help centers
  - FAQs

- Source Code Documentation
  - JSDoc
  - Python docstrings
  - JavaDoc
  - Doxygen

## Configuration

### Main Configuration (config.yaml)

```yaml
crawler:
  concurrent_requests: 5
  requests_per_second: 10
  max_retries: 3
  request_timeout: 30

processing:
  allowed_tags:
    - p
    - h1
    - h2
    - code
  code_languages:
    - python
    - javascript
  max_content_length: 5000000

quality:
  min_content_length: 100
  required_metadata_fields:
    - title
    - description
```

### Target Configuration (targets.yaml)

```yaml
- url: "https://docs.example.com/"
  depth: 2
  follow_external: false
  content_types:
    - "text/html"
    - "text/markdown"
  exclude_patterns:
    - "/downloads/"
    - "/community/"
  required_patterns:
    - "/docs/"
    - "/api/"
```

For detailed configuration options and examples, see the [User Guide](docs/user_guide.md).

## Testing

The project has comprehensive test coverage with 598+ tests:

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html

# Run specific test categories
uv run pytest tests/url/          # URL handling tests
uv run pytest tests/backends/     # Backend tests
uv run pytest tests/integration/  # Integration tests
```

## Requirements

### Core Dependencies
- **Python 3.9+** (tested on 3.9, 3.10, 3.11, 3.12)
- **Core Libraries**:
  ```
  aiohttp>=3.9.1          # Async HTTP client
  beautifulsoup4>=4.12.2  # HTML parsing
  pydantic>=2.5.2         # Data validation
  scrapy>=2.11.0          # Web crawling framework
  tldextract>=3.1.0       # Domain parsing
  ```

### Optional Backend Dependencies
- **Crawl4AI**: `crawl4ai>=0.2.0`
- **Playwright**: `playwright>=1.40.0`
- **Development**: `pytest`, `ruff`, `coverage`

Full dependency specifications in `pyproject.toml`.

## Architecture

### 🏗️ **Modular Design**

```
src/
├── backends/           # Pluggable scraping backends
├── crawler/           # Core crawling logic
├── processors/        # Content processing pipeline
├── utils/url/         # Advanced URL handling
├── organizers/        # Documentation organization
├── ui/               # Web interface
└── main.py           # Application entry point
```

### 🔧 **Core Components**

1. **Backend System** (`src/backends/`)
   - Pluggable architecture with automatic backend selection
   - Support for multiple scraping engines (Crawl4AI, Playwright, Scrapy)
   - Intelligent fallback and load balancing

2. **URL Processing** (`src/utils/url/`)
   - RFC-compliant URL normalization and validation
   - Security checks (path traversal, malicious URLs)
   - Domain classification and TLD extraction

3. **Content Pipeline** (`src/processors/`)
   - Structure-aware content extraction
   - Metadata enrichment and validation
   - Quality scoring and filtering

4. **Quality Assurance** (`src/processors/quality_checker.py`)
   - Automated content validation
   - Link verification and health checks
   - Duplicate detection and deduplication

## Development

### Setting Up Development Environment
```bash
# Clone and setup
git clone https://github.com/yourusername/lib2docscrape.git
cd lib2docscrape
uv sync --extra dev

# Run tests
uv run pytest

# Code quality checks
uv run ruff check src/
uv run ruff format src/
```

### Project Status
- ✅ **598 tests passing** (100% success rate)
- ✅ **Comprehensive backend support** (6 different backends)
- ✅ **Advanced URL handling** with security validation
- ✅ **Quality assurance pipeline** with automated checks
- 🔄 **Active development** with regular improvements

## Contributing

We welcome contributions! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/amazing-feature`
3. **Follow TDD**: Write tests first, then implement features
4. **Run quality checks**: `uv run ruff check && uv run pytest`
5. **Commit changes**: Use conventional commit messages
6. **Push to branch**: `git push origin feature/amazing-feature`
7. **Create Pull Request**

### Development Guidelines
- Follow Test-Driven Development (TDD)
- Maintain 100% test pass rate
- Use type hints and docstrings
- Follow the existing code style (ruff formatting)

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support & Documentation

- 📖 **[User Guide](docs/user_guide.md)** - Comprehensive usage documentation
- 🔧 **[API Documentation](docs/)** - Technical reference
- 🐛 **[Issue Tracker](https://github.com/yourusername/lib2docscrape/issues)** - Bug reports and feature requests
- 💬 **[Discussions](https://github.com/yourusername/lib2docscrape/discussions)** - Community support

---

**lib2docScrape** - *Comprehensive documentation scraping made simple*

