# lib2docScrape Project Structure

## Overview

lib2docScrape is a comprehensive documentation crawling and processing library designed to extract and analyze documentation from various sources. This document outlines the current project structure and describes the purpose of each component.

## Project Layout

The project is organized into several main directories:

-   **`.` (Root Directory):**
    Contains primary configuration files (e.g., [`config.yaml`](config.yaml:0), [`requirements.txt`](requirements.txt:0), [`setup.py`](setup.py:0)), main execution scripts (e.g., [`run.py`](run.py:0) for the crawler, [`run_gui.py`](run_gui.py:0) for the web interface), top-level documentation ([`README.md`](README.md:0)), and test invocation scripts.

-   **`src/` (Source Code):**
    This is the heart of the application, containing all Python modules. Key components include:
    -   [`crawler.py`](src/crawler.py:0): Implements the core web crawling logic.
    -   `backends/`: Contains modules for fetching content from different types of sources (e.g., [`crawl4ai.py`](src/backends/crawl4ai.py:0) for AI-assisted crawling, [`http_backend.py`](src/backends/http_backend.py:0) for standard HTTP/S).
    -   `processors/`: Houses modules responsible for processing the crawled content, such as extracting text, metadata, or checking quality (e.g., [`content_processor.py`](src/processors/content_processor.py:0)).
    -   `utils/`: A collection of utility functions and helper classes. This includes `url/` for specialized URL parsing, validation, and manipulation, and [`helpers.py`](src/utils/helpers.py:0) for general-purpose utilities.
    -   `gui/`: Contains the Flask web application ([`app.py`](src/gui/app.py:0)) providing a graphical user interface for interacting with the crawler.
    -   `models/`: Defines data structures and models used throughout the application (e.g., [`quality.py`](src/models/quality.py:0) for quality assessment metrics).
    -   `organizers/`: Logic for structuring and organizing the extracted documentation (e.g., [`doc_organizer.py`](src/organizers/doc_organizer.py:0)).
    -   [`main.py`](src/main.py:0): Serves as a primary entry point for certain operational modes of the application.
    -   [`backend_selector.py`](src/backend_selector.py:0): Logic for dynamically selecting the appropriate backend based on the target.
    -   [`simple_api.py`](src/simple_api.py:0): Provides a basic API interface for programmatic access.

-   **`tests/` (Tests):**
    Contains all automated tests for the project. The structure within `tests/` generally mirrors `src/` to ensure comprehensive coverage of all modules and functionalities (e.g., [`test_crawler.py`](tests/test_crawler.py:0), [`test_content_processor.py`](tests/test_content_processor.py:0)).

-   **`docs/` (Documentation):**
    General project documentation, including design documents, architecture overviews, and user guides. (This [`PROJECT_STRUCTURE.md`](PROJECT_STRUCTURE.md:0) file would ideally reside here or be linked).

-   **`cline_docs/` (Cline Tool Documentation):**
    Specific documentation related to the integration and usage of the Cline tool with this project, such as roadmaps ([`projectRoadmap.md`](cline_docs/projectRoadmap.md:0)) and task tracking ([`currentTask.md`](cline_docs/currentTask.md:0)).

-   **`examples/` (Examples):**
    Provides example scripts, configurations, or use-cases to help users understand how to use `lib2docScrape`.

-   **`static/` (Static Assets):**
    Contains static files like CSS, JavaScript, and images used by the `gui/` web interface.

-   **`templates/` (HTML Templates):**
    HTML templates used by the Flask application in `gui/` to render web pages.

-   **`archive/` (Archive):**
    Used for storing archived outputs, old logs, or other historical data.

-   **`lib2docscrape.egg-info/` (Packaging Info):**
    Directory generated during the packaging process (e.g., by `setuptools`), containing metadata about the package.

This structure aims to keep the codebase organized, maintainable, and easy to navigate.
