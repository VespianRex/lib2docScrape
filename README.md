# Lib2DocScrape

A powerful documentation scraping tool that automatically discovers, crawls, processes, and organizes technical documentation from various sources. Built with intelligent content extraction and organization capabilities, it helps you collect and structure documentation efficiently.

## Features

- **Documentation Discovery & Extraction**
  - Automatic detection of documentation sections
  - Support for multiple documentation formats (HTML, Markdown, RST)
  - Smart content structure preservation
  - Code block and syntax highlighting extraction

- **Multi-Backend Support**
  - Primary: Crawl4AI for efficient documentation crawling
  - Selenium for JavaScript-rendered documentation
  - Scrapy for high-performance needs
  - File system backend for local documentation

- **Content Processing**
  - Intelligent structure detection
  - Metadata extraction
  - Cross-reference preservation
  - Asset handling (images, PDFs, etc.)

- **Documentation Organization**
  - Automatic categorization
  - Version detection and tracking
  - Cross-reference management
  - Search index generation

## Installation

1. Ensure you have Python 3.11 or higher installed
   ```bash
   python --version
   ```

2. Install Lib2DocScrape via pip:
   ```bash
   pip install lib2docscrape
   ```

3. Verify installation:
   ```bash
   lib2docscrape --version
   ```

## Quick Start

### CLI Usage

1. Basic documentation scraping:
   ```bash
   lib2docscrape scrape https://docs.example.com
   ```

2. Using custom configuration:
   ```bash
   lib2docscrape scrape -c config.yaml -t targets.yaml
   ```

3. Start web interface:
   ```bash
   lib2docscrape serve
   ```

### Web Interface

1. Access the web interface at `http://localhost:8000`
2. Use the dashboard to:
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

## Requirements

- Python 3.11+
- Key dependencies:
  ```
  aiohttp>=3.9.1
  beautifulsoup4>=4.12.2
  pydantic>=2.5.2
  markdownify>=0.11.6
  bleach>=6.0.0
  fastapi>=0.109.0
  selenium>=4.16.0
  scrapy>=2.11.0
  ```

Full dependencies list in `requirements.txt`.

## Architecture

### Core Components

1. **Backend System**
   - Pluggable architecture for different scraping methods
   - Intelligent backend selection based on content type
   - Load balancing and failover support

2. **Content Processors**
   - Structure preservation
   - Metadata extraction
   - Asset handling
   - Cross-reference management

3. **Quality Assurance**
   - Content validation
   - Link checking
   - Metadata verification

4. **Documentation Organization**
   - Automatic categorization
   - Version management
   - Search indexing

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

1. Check the [User Guide](docs/user_guide.md)
2. Search [existing issues](https://github.com/yourusername/lib2docscrape/issues)
3. Create a new issue if needed

---

*Last Updated: May 15, 2025*