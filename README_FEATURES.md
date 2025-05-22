# lib2docScrape Features

This document describes the key features of the lib2docScrape system.

## Core Features

### Documentation Scraping

- **Multi-backend Support**: Supports multiple scraping backends (HTTP, Crawl4AI, Lightpanda)
- **Configurable Crawling**: Control depth, follow patterns, and content types
- **JavaScript Rendering**: Process JavaScript-rendered content
- **Rate Limiting**: Respect website rate limits
- **Error Handling**: Robust error handling and retry mechanisms

### Content Processing

- **HTML Parsing**: Extract structured content from HTML
- **Metadata Extraction**: Extract titles, descriptions, and other metadata
- **Content Cleaning**: Remove boilerplate and irrelevant content
- **Code Extraction**: Identify and extract code samples
- **Image Processing**: Handle and store images

### Quality Checking

- **Content Validation**: Ensure content meets quality standards
- **Link Validation**: Check for broken links
- **Completeness Checking**: Verify all required content is present
- **Consistency Checking**: Ensure consistent formatting and structure

### Storage

- **Flexible Storage**: Store content in various formats (JSON, HTML, Markdown)
- **Versioning**: Track changes across library versions
- **Compression**: Optimize storage with compression
- **Indexing**: Index content for efficient retrieval

### Library Management

- **Version Tracking**: Track multiple versions of libraries
- **Comparison**: Compare documentation across versions
- **Visualization**: Visualize version history and changes
- **Registry**: Maintain a registry of tracked libraries

## Advanced Features

### Distributed Crawling

The distributed crawling system allows for parallel processing of crawl targets using multiple workers.

#### Key Components:

- **Manager**: Coordinates workers and distributes tasks
- **Workers**: Process crawl tasks independently
- **Task Queue**: Prioritized queue for crawl tasks
- **Result Aggregation**: Collect and process results from workers

#### Usage:

```bash
python -m src.main scrape -t targets.yaml -d -w 5
```

This command starts a distributed crawl with 5 workers.

### Compressed Storage

The compressed storage system optimizes storage by compressing content before saving.

#### Supported Compression Formats:

- **GZIP**: Standard compression format
- **LZMA**: High compression ratio
- **BZ2**: Alternative compression algorithm
- **ZLIB**: Fast compression

#### Usage:

```python
from src.storage.compressed import CompressedStorage, CompressionConfig, CompressionFormat

# Create storage with GZIP compression
config = CompressionConfig(format=CompressionFormat.GZIP, level=9)
storage = CompressedStorage(config=config)

# Save and load JSON data
storage.save_json(data, "data.json")
loaded_data = storage.load_json("data.json")

# Save and load pickled data
storage.save_pickle(data, "data.pkl")
loaded_data = storage.load_pickle("data.pkl")
```

### NLP Processing

The NLP processing system provides tools for analyzing documentation content.

#### Document Categorization:

```bash
python -m src.main library categorize -n library_name -c 10
```

This command categorizes documentation for a library into 10 categories.

#### Topic Modeling:

```bash
python -m src.main library topics -n library_name -t 10
```

This command extracts 10 topics from library documentation.

### Improved User Interface

The improved user interface provides a web-based dashboard for monitoring and controlling the system.

#### Components:

- **Dashboard**: Overview of system status and activity
- **Search Interface**: Search documentation content
- **Visualizations**: Interactive charts and graphs
- **Admin Panel**: System administration and monitoring

#### Usage:

```bash
python -m src.main serve -p 8000
```

This command starts the web server on port 8000.

## Package Management

The package management system provides tools for managing Python packages.

#### Usage:

```bash
# Install a package
python -m src.main library package install package_name

# Uninstall a package
python -m src.main library package uninstall package_name

# List installed packages
python -m src.main library package list
```

## Version History Visualization

The version history visualization system provides interactive visualizations of library version history.

#### Usage:

```bash
python -m src.main library visualize -n library_name
```

This command generates an HTML visualization of the library version history.

## Testing

The system includes comprehensive testing with high code coverage.

#### Test Types:

- **Unit Tests**: Test individual components
- **Integration Tests**: Test component interactions
- **Property-Based Tests**: Test with randomly generated inputs
- **Benchmark Tests**: Test performance

#### Running Tests:

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=src

# Run specific test file
pytest tests/path/to/test_file.py
```
