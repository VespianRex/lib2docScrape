# lib2docScrape Project Structure

## Overview

lib2docScrape is a comprehensive documentation crawling and processing library designed to extract and analyze documentation from various sources. This document outlines the current project structure and describes the purpose of each component.

## Current Directory Structure with OLD Files Analysis

```
.
|-- .pytest_cache
|-- PROJECT_STRUCTURE.md
|-- README.md
|-- README_MAC.md
|-- archive
|-- config.yaml
|-- crawler.log
|-- examples
|-- find_duplicates.py
|-- lib2doc
|-- lib2docscrape.egg-info
|-- output.json
|-- pyprojectOLD.toml
|-- pytest_html_report.html
|-- report.html
|-- requirements.txt
|-- run.py
|-- run_gui.py
|-- run_tests.py
|-- setup.py
|-- src
|-- srs.md
|-- start_crawler.sh
|-- start_simple_crawler.sh
|-- static
|-- targets.yaml
|-- templates
`-- tests

src
|-- __init__OLD_347.py
|-- __pycache__
|   |-- __init__.cpython-311OLD.pyc
|   |-- crawler.cpython-311.pyc
|   `-- main.cpython-311.pyc
|-- apiOLD_892.py
|-- backend_selector.py
|-- backends
|   |-- __init__.py
|   |-- __pycache__
|   |   |-- __init__.cpython-311.pyc
|   |   |-- base.cpython-311OLD.pyc
|   |   |-- crawl4ai.cpython-311.pyc
|   |   |-- html.cpython-311OLD.pyc
|   |   |-- http.cpython-311.pyc
|   |   |-- http_backend.cpython-311.pyc
|   |   `-- selector.cpython-311.pyc
|   |-- baseOLD_478.py
|   |-- crawl4ai.py
|   |-- htmlOLD_623.py
|   |-- http.py
|   |-- http_backend.py
|   `-- selector.py
|-- baseOLD_156.py
|-- content_processorOLD_734.py
|-- crawler.py
|-- gui
|   |-- __init__OLD_291.py
|   |-- __pycache__
|   |   |-- __init__.cpython-311OLD.pyc
|   |   `-- app.cpython-311.pyc
|   |-- app.py
|   |-- static
|   `-- templates
|       `-- indexOLD.html
|-- lib2docscrape.egg-info
|   |-- PKG-INFOOLD
|   |-- SOURCESOLD.txt
|   |-- dependency_linksOLD.txt
|   `-- top_levelOLD.txt
|-- main.py
|-- models
|   |-- quality.py
|   `-- url.py
|-- organizers
|   |-- __pycache__
|   |   `-- doc_organizer.cpython-311.pyc
|   `-- doc_organizer.py
|-- processors
|   |-- __pycache__
|   |   |-- content_processor.cpython-311.pyc
|   |   `-- quality_checker.cpython-311.pyc
|   |-- content_processor.py
|   `-- quality_checker.py
|-- simple_api.py
`-- utils
    |-- __pycache__
    |   `-- helpers.cpython-311.pyc
    `-- helpers.py

tests
|-- __pycache__
|   |-- conftest.cpython-311-pytest-8.3.3.pyc
|   |-- test_base.cpython-311-pytest-8.3.3.pyc
|   |-- test_content_processor_advanced.cpython-311-pytest-8.3.3.pyc
|   |-- test_crawl4ai.cpython-311-pytest-8.3.3.pyc
|   |-- test_crawl4ai_extended.cpython-311-pytest-8.3.3.pyc
|   |-- test_crawler.cpython-311-pytest-8.3.3.pyc
|   |-- test_crawler_advanced.cpython-311-pytest-8.3.3.pyc
|   |-- test_integration.cpython-311-pytest-8.3.3.pyc
|   |-- test_organizer.cpython-311-pytest-8.3.3.pyc
|   |-- test_processor.cpython-311-pytest-8.3.3.pyc
|   |-- test_quality.cpython-311-pytest-8.3.3.pyc
|   `-- test_url_handling.cpython-311-pytest-8.3.3.pyc
|-- conftestOLD.py
|-- test_baseOLD.py
|-- test_content_processor_advanced.py
|-- test_content_processor_edge.py
|-- test_crawl4ai.py
|-- test_crawl4ai_extended.py
|-- test_crawler.py
|-- test_crawler_advanced.py
|-- test_gui.py
|-- test_helpers.py
|-- test_integration.py
|-- test_integration_advanced.py
|-- test_organizer.py
|-- test_processor.py
|-- test_quality.py
`-- test_url_handling.py

.pytest_cache
|-- .gitignore
|-- CACHEDIR.TAG
|-- READMEOLD.md
`-- v
    `-- cache
        |-- lastfailed
        |-- nodeids
        `-- stepwise
```

## File Descriptions

### Root Directory Files

- `PROJECT_STRUCTURE.md`: This file - documents the project structure
- `README.md`: Main project documentation
- `README_MAC.md`: macOS-specific instructions
- `config.yaml`: Configuration settings for the crawler
- `crawler.log`: Log file for crawler operations
- `find_duplicates.py`: Script to identify duplicate content
- `output.json`: Output file for crawler results
- `requirements.txt`: Python package dependencies
- `run.py`: Main script to run the crawler
- `run_gui.py`: Script to launch the GUI interface
- `run_tests.py`: Script to run test suite
- `setup.py`: Project installation configuration
- `srs.md`: Software Requirements Specification
- `start_crawler.sh`: Shell script to start crawler
- `start_simple_crawler.sh`: Shell script for simple crawler mode
- `targets.yaml`: Target URLs configuration

### Source Files (src/)

#### Core Files

- `main.py`: Application entry point
- `crawler.py`: Main crawler implementation
- `backend_selector.py`: Backend selection logic
- `simple_api.py`: Simplified API interface

#### Modules

- `models/quality.py`: Quality assessment models
- `models/url.py`: URL handling and processing
- `processors/content_processor.py`: Content processing logic
- `processors/quality_checker.py`: Quality checking implementation
- `organizers/doc_organizer.py`: Document organization logic
- `utils/helpers.py`: Helper utilities

#### OLD Files (Previous Versions)

- `__init__OLD_347.py`, `__init__.cpython-311OLD.pyc`: Old initialization files
- `apiOLD_892.py`: Previous API implementation
- `baseOLD_156.py`, `baseOLD_478.py`: Old base classes
- `content_processorOLD_734.py`: Previous content processor
- `htmlOLD_623.py`: Old HTML processing
- `gui/__init__OLD_291.py`: Old GUI initialization
- `gui/templates/indexOLD.html`: Previous GUI template

### Test Files (tests/)

#### Main Test Files

- `test_content_processor_advanced.py`: Advanced content processor tests
- `test_content_processor_edge.py`: Edge case tests
- `test_crawl4ai.py`, `test_crawl4ai_extended.py`: Crawler AI tests
- `test_crawler.py`, `test_crawler_advanced.py`: Crawler functionality tests
- `test_gui.py`: GUI testing
- `test_integration.py`, `test_integration_advanced.py`: Integration tests
- `test_organizer.py`: Document organizer tests
- `test_processor.py`: Processor tests
- `test_quality.py`: Quality assessment tests
- `test_url_handling.py`: URL handling tests

#### OLD Test Files

- `conftestOLD.py`: Previous pytest configuration
- `test_baseOLD.py`: Old base test cases

## Proposed Directory Structure

```
lib2docScrape/
├── src/
│   ├── core/                # Core functionality
│   │   ├── crawler/
│   │   │   ├── base.py     # Merged from baseOLD.py
│   │   │   └── crawler.py  # Current crawler.py
│   │   ├── backends/
│   │   │   ├── base.py     # From backends/baseOLD.py
│   │   │   ├── http.py     # Merged http.py + http_backend.py
│   │   │   └── crawl4ai.py # Current AI crawler
│   │   └── processors/
│   │       ├── base.py     # New base processor
│   │       ├── content.py  # Merged content processors
│   │       └── quality.py  # From quality_checker.py
│   │
│   ├── interface/
│   │   ├── api/
│   │   │   ├── routes.py   # Merged from apiOLD.py + simple_api.py
│   │   │   └── handlers.py # New handlers
│   │   ├── cli/
│   │   │   └── commands.py # New CLI interface
│   │   └── gui/
│   │       ├── app.py      # Current GUI app
│   │       └── views.py    # New view components
│   │
│   └── common/
│       ├── models/         # Current models
│       ├── utils/          # Current utils
│       └── organizers/     # Current organizers
│
├── tests/                  # Test suite
├── docs/                   # Documentation
├── examples/               # Usage examples
└── static/                # Static assets

```

## Implementation Plan

1. Create new directory structure
2. Migrate critical files first:
   - Move and merge backend base classes
   - Consolidate content processors
   - Merge API implementations
3. Review and migrate HTML backend
4. Remove safe-to-delete files
5. Update all import statements
6. Run comprehensive test suite
7. Validate functionality

## Notes

- All OLD files contain some functionality that needs review
- Some files contain critical models and base classes
- Careful migration needed to preserve functionality
- Test coverage must be maintained throughout
- Documentation should be updated after migration
