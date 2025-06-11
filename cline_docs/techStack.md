# Technology Stack
Last Updated: 2025-05-23 12:05

## Testing Framework
- pytest - Main testing framework
- coverage.py - Code coverage measurement
- UV - Package manager for dependency management

## Main Project Technologies
- Python - Primary programming language
- HTTP Backend - `aiohttp` for asynchronous web scraping and API interactions
- GUI Components - `FastAPI` for the web API and `Jinja2` for templating

## Development Tools
- pytest-html - For test reporting
- pytest.ini - Test configuration
- conftest.py - Test fixtures and configuration

## Project Structure
### Core Components
- src/ - Main source code
- tests/ - Test suite
- examples/ - Example implementations
- static/ - Static resources
- templates/ - HTML templates

### Key Dependencies
- aiohttp - Asynchronous HTTP client
- beautifulsoup4 - HTML parsing
- pydantic - Data validation and settings management
- markdownify - HTML to Markdown conversion
- pytest - Testing framework
- uv - Package manager
- tldextract - Extracting TLD, domain, and subdomain from URLs
- idna - Internationalized Domain Names support

## Architecture Decisions
- Modular design with separate processors for different content types
- Backend selector pattern for flexibility
- Document-centric processing approach