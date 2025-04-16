# Plan to Fix URL Normalization Tests

This plan outlines the steps to fix the failing tests in `tests/test_url_handling.py` by refining the normalization logic in `src/utils/url_info.py`.

## Target File
`src/utils/url_info.py`

## Issues Identified
The failing tests indicate problems in:
1.  **Path Normalization:** Handling relative segments (`.` and `..`), multiple slashes (`//`), and trailing slashes.
2.  **Query String Handling:** Ensuring a `/` exists between the domain and the query string when the path is otherwise empty.
3.  **Hostname Normalization:** Correctly converting internationalized domain names (IDN) to Punycode.

## Proposed Changes

### 1. Refine Path Normalization (`_normalize_path` method)
Implement the following steps:
1.  **Unquote:** Use `unquote_plus` on the input path.
2.  **Normalize `.` and `..`:** Apply `posixpath.normpath` to the *unquoted* path.
3.  **Handle Leading Slash:** Ensure the result starts with `/` if the original path did.
4.  **Handle Empty/`.` Path:** Set the result to `/` if it's empty or just `.`.
5.  **Remove Duplicate Slashes:** Replace `//` with `/` iteratively.
6.  **Preserve Trailing Slash:** Append `/` if `_original_path_had_trailing_slash` is true and the path isn't just `/`.
7.  **Re-encode:** Use `urllib.parse.quote` with `PATH_SAFE_CHARS`.

### 2. Correct Hostname Normalization (`_normalize` method)
Implement the following steps:
1.  **Extract Hostname:** Get from `self._parsed.hostname`.
2.  **Handle None/Empty:** Skip if hostname is missing.
3.  **Lowercase:** Convert to lowercase.
4.  **IDNA Encoding (Punycode):**
    *   If non-ASCII, encode using `idna.encode().decode('ascii')`.
    *   If ASCII, use the lowercased version.
    *   Handle potential `idna.IDNAError` (e.g., log warning, fallback to lowercase).
5.  **Construct `netloc_norm`:** Combine normalized hostname and non-default port.

### 3. Simplify Query/Slash Handling (`_normalize` method)
Implement the following steps:
1.  **Normalize Query:** Use `parse_qsl` (preserving order/blanks) and `urlencode` (consistent encoding).
2.  **Ensure Path for `urlunparse`:** If the normalized path (`path_norm`) resulting from `_normalize_path` is empty, explicitly set it to `/`.
3.  **Remove Manual Slash Logic:** Delete the code block from lines 378-393.
4.  **Assemble Final URL:** Use `urlunparse` with all normalized components (scheme, netloc, path (now >= '/'), params, query, empty fragment).