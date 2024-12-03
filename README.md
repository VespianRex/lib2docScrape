# Lib2DocScrape

An autonomous documentation crawler system built around Crawl4AI, with support for multiple backends and adaptive crawling capabilities. This system automatically discovers, crawls, processes, and organizes technical documentation from various sources, with intelligent backend selection and self-optimization capabilities.

## Features

- **Multi-Backend Support**
  - Primary Backend: Crawl4AI
  - Secondary Backends:
    - Selenium (for JavaScript-heavy sites)
    - Scrapy (for high-performance needs)
    - Custom adapters for specialized cases
  - Intelligent backend selection based on content type and site complexity

- **Core Components**
  - Backend Manager: Dynamic backend selection and load balancing
  - Content Processor: Multi-format support and structure preservation
  - Documentation Organizer: Automatic categorization and versioning
  - Quality Assurance: Content validation and link checking

- **Intelligence Layer**
  - Smart Crawling: Priority-based strategies and depth optimization
  - Pattern Recognition: Documentation structure learning
  - Adaptive Behavior: Performance optimization and self-healing

## Requirements

- Python 3.11 or higher
- Required packages (install via pip):
  ```
  aiohttp>=3.9.1
  beautifulsoup4>=4.12.2
  selenium>=4.16.0
  scrapy>=2.11.0
  redis>=5.0.1
  sqlalchemy>=2.0.23
  fastapi>=0.109.0
  uvicorn>=0.25.0
  python-dotenv>=1.0.0
  pydantic>=2.5.3
  httpx>=0.26.0
  pytest>=7.4.3
  pytest-asyncio>=0.23.2
  pytest-cov>=4.1.0
  black>=23.12.1
  isort>=5.13.2
  mypy>=1.8.0
  ruff>=0.1.9
  ```

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/lib2docscrape.git
   cd lib2docscrape
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Configuration

The system uses two main configuration files:

1. `config.yaml`: Main configuration file that controls crawler behavior, processing rules, and quality checks.
2. `targets.yaml`: Defines the documentation sites to crawl and their specific parameters.

### Main Configuration (config.yaml)

The configuration file is divided into several sections:

- **crawler**: General crawler settings
  - concurrent_requests: Number of concurrent requests
  - requests_per_second: Rate limiting
  - max_retries: Maximum retry attempts
  - request_timeout: Request timeout in seconds

- **processing**: Content processing rules
  - allowed_tags: HTML tags to preserve
  - code_languages: Supported programming languages
  - max_content_length: Maximum content size

- **quality**: Quality assurance settings
  - min_content_length: Minimum content length
  - max_broken_links_ratio: Maximum allowed broken links
  - required_metadata_fields: Required metadata fields

- **organization**: Documentation organization rules
  - category_rules: Rules for categorizing content
  - max_versions_to_keep: Version history limit

### Targets Configuration (targets.yaml)

Define documentation sources to crawl:

```yaml
- url: "https://docs.example.com/"
  depth: 2
  follow_external: false
  content_types:
    - "text/html"
  exclude_patterns:
    - "/download/"
    - "/community/"
  required_patterns:
    - "/docs/"
    - "/api/"
  max_pages: 1000
```

## Usage

1. Configure your crawl targets in `targets.yaml`

2. Run the crawler:
   ```bash
   python -m src.main -c config.yaml -t targets.yaml
   ```

Additional options:
- `-v, --verbose`: Enable verbose logging
- `-c, --config`: Specify configuration file path
- `-t, --targets`: Specify targets file path

## Output

The crawler generates the following outputs:

1. Crawl results in JSON format:
   - Document content and structure
   - Quality metrics and issues
   - Crawl statistics

2. Log file with crawl progress and errors

3. Organized documentation:
   - Categorized content
   - Cross-references
   - Search indices

## Architecture

### Backend System

The crawler uses a pluggable backend system:

1. **Crawl4AI Backend**
   - Primary backend for most documentation sites
   - Handles standard HTML content
   - Efficient and lightweight

2. **Selenium Backend**
   - For JavaScript-heavy sites
   - Handles dynamic content
   - Full browser automation

3. **Scrapy Backend**
   - High-performance crawling
   - Distributed crawling support
   - Custom middleware support

### Processing Pipeline

1. Content Extraction
   - HTML parsing and cleaning
   - Structure preservation
   - Code block handling

2. Quality Checks
   - Content validation
   - Link checking
   - Format verification

3. Organization
   - Automatic categorization
   - Version tracking
   - Search index generation

## Performance

The system is designed to meet the following performance targets:

- Concurrent crawling: 50+ pages/second
- Response time: < 100ms for backend switching
- Processing time: < 1s per page
- Memory usage: < 1GB per crawler instance

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Built with inspiration from various documentation systems
- Uses multiple open-source libraries and tools
- Community contributions and feedback

## Support

For support, please:
1. Check the documentation
2. Search existing issues
3. Create a new issue if needed

---

*Last Updated: January 2024*