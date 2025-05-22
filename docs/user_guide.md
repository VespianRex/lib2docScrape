# Documentation Scraping User Guide

## Overview

Lib2DocScrape is a powerful documentation scraping tool that automatically discovers, crawls, processes, and organizes technical documentation from various sources. This guide will help you get started with using the tool effectively.

## Table of Contents

1. [Installation](#installation)
2. [Basic Usage](#basic-usage)
3. [Configuration](#configuration)
4. [Best Practices](#best-practices)
5. [Troubleshooting](#troubleshooting)

## Installation

1. Ensure you have Python 3.11 or higher installed
2. Install Lib2DocScrape:
   ```bash
   pip install lib2docscrape
   ```
3. Verify installation:
   ```bash
   lib2docscrape --version
   ```

## Basic Usage

### Command Line Interface

1. Basic scraping:
   ```bash
   lib2docscrape scrape https://docs.example.com
   ```

2. Scrape with custom config:
   ```bash
   lib2docscrape scrape -c config.yaml https://docs.example.com
   ```

3. Multiple targets:
   ```bash
   lib2docscrape scrape -t targets.yaml
   ```

### Web Interface

1. Start the web server:
   ```bash
   lib2docscrape serve
   ```

2. Open your browser and navigate to `http://localhost:8000`
3. Use the web interface to:
   - Configure scraping targets
   - Monitor scraping progress
   - View and organize scraped documentation
   - Export documentation in various formats

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
    - h3
    - code
    - pre
  code_languages:
    - python
    - javascript
    - bash
  max_content_length: 5000000

quality:
  min_content_length: 100
  max_broken_links_ratio: 0.1
  required_metadata_fields:
    - title
    - description

organization:
  category_rules:
    - pattern: "/api/"
      category: "API Documentation"
    - pattern: "/guide/"
      category: "User Guide"
  max_versions_to_keep: 5
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

### Environment Variables

- `LIB2DOCSCRAPE_CONFIG`: Default configuration file path
- `LIB2DOCSCRAPE_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `LIB2DOCSCRAPE_OUTPUT_DIR`: Directory for scraped documentation
- `LIB2DOCSCRAPE_CACHE_DIR`: Directory for caching scraped content

## Best Practices

1. **Start Small**
   - Begin with a small subset of documentation
   - Test configuration on sample pages
   - Gradually increase scope

2. **Optimize Performance**
   - Adjust concurrent requests based on server capacity
   - Use appropriate rate limiting
   - Enable caching for repeated scrapes

3. **Content Organization**
   - Define clear category rules
   - Use meaningful file patterns
   - Maintain consistent versioning

4. **Quality Control**
   - Set appropriate content length thresholds
   - Configure required metadata
   - Monitor broken links ratio

## Troubleshooting

### Common Issues

1. **Rate Limiting**
   - Symptom: Too many 429 responses
   - Solution: Decrease requests_per_second in config.yaml

2. **Missing Content**
   - Symptom: Expected content not scraped
   - Solutions:
     - Check content_types configuration
     - Verify required_patterns
     - Ensure JavaScript rendering is enabled if needed

3. **High Memory Usage**
   - Symptom: Process using excessive memory
   - Solutions:
     - Reduce concurrent_requests
     - Enable content size limits
     - Use incremental processing

4. **Broken Links**
   - Symptom: High number of broken internal links
   - Solutions:
     - Update URL patterns
     - Check site availability
     - Verify access permissions

### Debug Mode

Enable debug logging for detailed information:

```bash
export LIB2DOCSCRAPE_LOG_LEVEL=DEBUG
lib2docscrape scrape -v
```

### Support Resources

1. Check documentation at https://lib2docscrape.readthedocs.io/
2. Search existing issues on GitHub
3. Join our community Discord for help