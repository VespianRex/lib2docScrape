# Codebase Summary

## Key Components and Their Interactions

### Core Components
1. Processors
   - ContentProcessor: Handles content processing and extraction
   - DocumentProcessor: Manages document-level operations
   - HTMLProcessor: Processes HTML content
   - LinkProcessor: Handles URL and link processing
   - QualityChecker: Validates content quality

2. Backend System
   - BackendSelector: Manages different backend implementations
   - HTTP Backend: Handles web requests
   - Crawl4AI: Specialized crawler implementation

3. Models
   - Quality: Quality-related data structures
   - URL: URL handling and validation

### Data Flow
1. Input URL/Document → 
2. Backend Processing →
3. Content Extraction →
4. Document Organization →
5. Quality Validation

## External Dependencies
To be analyzed from requirements.txt

## Recent Significant Changes

### Backend Selector Refactoring
- Refactored `BackendSelector` to use the correct `URLInfo` class from `src/utils/url_info.py` for URL processing, replacing the deprecated `URLProcessor`.

### URL Handling Enhancement
- The URL handling implementation has been refactored to use `tldextract` library, providing the following benefits:
  - Proper domain parsing with awareness of public suffixes (e.g., `.co.uk`, `.org.za`)
  - Enhanced domain component extraction (subdomains, registered domain, TLD)
  - Maintained security validation from the original implementation
  - Performance improvements for URL processing operations

#### Migration Notes
- The new implementation is available through the standard import path: `from src.utils.helpers import URLInfo`
- Backward compatibility is maintained
- New properties available include:
  - `root_domain`: The domain name without suffix (e.g., "example" from "example.com")
  - `suffix`: The TLD suffix (e.g., "co.uk" from "example.co.uk")
  - `registered_domain`: Domain + suffix without subdomains
  - `subdomain`: Just the subdomain part of the URL

## External Dependencies
- `tldextract`: For accurate domain parsing using the Public Suffix List
- `idna`: For proper handling of internationalized domain names

## User Feedback Integration
Will be updated based on test results and fixes
