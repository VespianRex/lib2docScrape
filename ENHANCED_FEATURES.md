# Enhanced Features for lib2docScrape

This document describes the new features added to the lib2docScrape tool.

## 1. Lightpanda Backend

A new backend has been added that uses the Lightpanda browser for JavaScript-heavy documentation sites. Lightpanda is an AI-native web browser with minimal memory footprint, making it ideal for documentation scraping.

### Installation

1. Download the Lightpanda binary:

   ```bash
   # For Linux
   curl -L -o lightpanda https://github.com/lightpanda-io/browser/releases/download/nightly/lightpanda-x86_64-linux && \
   chmod a+x ./lightpanda

   # For MacOS
   curl -L -o lightpanda https://github.com/lightpanda-io/browser/releases/download/nightly/lightpanda-aarch64-macos && \
   chmod a+x ./lightpanda
   ```

2. Make sure the binary is in your PATH or specify the full path in the configuration.

### Configuration

Add the following to your `config.yaml` file:

```yaml
lightpanda:
  executable_path: "lightpanda"  # Or full path to the binary
  host: "127.0.0.1"
  port: 9222
  timeout: 30.0
  max_retries: 3
  wait_for_load: true
  wait_time: 2.0
  javascript_enabled: true
  user_agent: "Lib2DocScrape/1.0 (Lightpanda) Documentation Crawler"
  viewport_width: 1280
  viewport_height: 800
  extra_args: []
```

### Usage

```bash
# Use Lightpanda backend for crawling
lib2docscrape scrape -c config.yaml -t targets.yaml --backend lightpanda
```

## 2. Backend Benchmarking

A new benchmarking module has been added to compare the performance of different backends.

### Usage

```bash
# Benchmark all available backends
lib2docscrape benchmark -u https://docs.python.org/3/ -b all

# Benchmark specific backends
lib2docscrape benchmark -u https://docs.python.org/3/,https://docs.djangoproject.com/en/stable/ -b http,lightpanda -o benchmark_report.md
```

### Output

The benchmark generates a Markdown report with performance metrics for each backend, including:

- Crawl time
- Success rate
- Content size
- Memory usage

If matplotlib is installed, it also generates charts comparing the backends.

## 3. Library Version Tracking

A new module has been added to track and compare different versions of library documentation.

### Usage

```bash
# Track multiple versions of a library
lib2docscrape library track -n python -v 3.9,3.10,3.11

# Compare two versions
lib2docscrape library compare -n python -v1 3.9 -v2 3.10 -o python_diff.md

# List tracked libraries
lib2docscrape library list

# List versions of a specific library
lib2docscrape library list -n python
```

### Features

- Automatically detects library versions from URLs
- Compares documentation between versions
- Generates diff reports showing added, removed, and modified pages
- Maintains a registry of known libraries and their documentation URLs

## 4. Documentation Site Verification

A new utility has been added to verify that a URL points to a valid documentation site and identify the library.

### Features

- Verifies if a URL points to a known documentation site
- Identifies the library and version from the URL or content
- Supports common documentation sites like Python, Django, Flask, React, etc.
- Can be extended with custom patterns

## 5. Command Line Interface Improvements

The command line interface has been restructured to use subcommands:

```bash
# Scrape documentation
lib2docscrape scrape -c config.yaml -t targets.yaml

# Start web server
lib2docscrape serve

# Benchmark backends
lib2docscrape benchmark -u https://docs.python.org/3/ -b all

# Track library versions
lib2docscrape library track -n python -v 3.9,3.10,3.11
```

## Example Configuration

A sample configuration file with all the new features is provided in `config_with_lightpanda.yaml`.

## Example Targets

A sample targets file for benchmarking is provided in `benchmark_targets.yaml`.
