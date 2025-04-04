# URL Handling Refactor Plan

## Goal
Consolidate URL parsing, validation, and normalization logic into a single, robust class to improve trackability, debuggability, and maintainability.

## Proposed Architecture: Unified `URLInfo` Class

1.  **New File & Class:** Create `src/utils/url_info.py` and define the `URLInfo` class within it.
2.  **Responsibilities (within `URLInfo`):**
    *   **Initialization (`__init__`)**: Takes raw URL and optional base URL. Stores `raw_url`. Calls `_parse_and_resolve()`, `_validate()`, and (if valid) `_normalize()`. Determines `url_type`. Stores results (`_parsed`, `_is_valid`, `_error_message`, `normalized_url`).
    *   **Parsing (`_parse_and_resolve`)**: Internal method using `urlparse` and `urljoin`.
    *   **Validation (`_validate`)**: Internal method orchestrating calls to smaller, private validation helper methods (e.g., `_validate_scheme`, `_validate_port`, `_validate_path`, etc.). Returns `(True, None)` or `(False, "Error Message")`.
    *   **Normalization (`_normalize`)**: Internal method orchestrating calls to smaller, private normalization helper methods (e.g., `_normalize_scheme_host`, `_normalize_port`, `_normalize_path`, etc.) that operate on and update the internal parsed representation. Removes fragment. Calls `urlunparse` at the end.
    *   **Properties**: Exposes `raw_url`, `normalized_url`, `is_valid`, `error_message`, `scheme`, `netloc`, `path`, `url_type`, etc.
3.  **Refactor `URLProcessor`:** Modify `URLProcessor.process_url` in `src/utils/helpers.py` to:
    *   Import `URLInfo` from `src.utils.url_info`.
    *   Create an instance: `url_info = URLInfo(url, base_url)`.
    *   Return this `url_info` instance.
4.  **Update Tests:** Adjust tests (`test_content_processor_advanced.py`, etc.) to:
    *   Import `URLInfo` from the new location.
    *   Assert `url_info.is_valid`, `url_info.normalized_url`, and `url_info.error_message` as appropriate.
5.  **Cleanup:** Delete the old `URLNormalizer` class and its file (`src/utils/url_utils.py`).

## Diagram (Mermaid)

```mermaid
graph TD
    A[Input URL, Optional Base URL] --> B(URLInfo.__init__ in url_info.py);
    B --> C{_parse_and_resolve};
    C --> D{_validate};
    D -- OK --> E{_normalize};
    D -- Error --> F[Store Error, _is_valid=False];
    E --> G[Store Normalized URL, _is_valid=True];
    F --> H[URLInfo Instance];
    G --> H;

    subgraph _validate
        direction LR
        V1[_validate_scheme] --> V2[_validate_port];
        V2 --> V3[_validate_path];
        V3 --> V4[_validate_query];
        V4 --> V5[_validate_netloc];
        V5 --> V6[_validate_security];
    end

    subgraph _normalize
        direction LR
        N1[_normalize_scheme_host] --> N2[_normalize_port];
        N2 --> N3[_normalize_path];
        N3 --> N4[_normalize_query];
        N4 --> N5[Remove Fragment];
        N5 --> N6[urlunparse];
    end

    subgraph URLInfo Instance
        direction LR
        P1[raw_url]
        P2[normalized_url]
        P3[is_valid]
        P4[error_message]
        P5[scheme]
        P6[netloc]
        P7[path]
        P8[url_type]
    end

    H --> I{Caller (e.g., URLProcessor)};
    I --> J[Check is_valid, access properties];