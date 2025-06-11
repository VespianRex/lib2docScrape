# Next Steps – URL‑Handling Roadmap

> **Owner:** `Qodo`  
> **Scope:** Everything related to the newly‑modular URL pipeline (security · parsing · normalization · classification · URLInfo façade).  
> **Time‑frame:** 3–4 incremental iterations (~2 weeks)  
> **TDD:** Mandatory for all development tasks (🔴 → 🟢 → 🔧)  

---

## 1  Validation & Regression Pass   *(Iteration 0)*

| # | Task | Sub‑tasks | Deliverable |
|---|------|-----------|-------------|
| 1.1 | Full test‑suite run | `pytest -q` and `pytest -q tests/url_handling_integration.py` | All tests 🔵 pass & baseline timings recorded |
| 1.2 | Static checks | `ruff`, `mypy` (strict for `src/utils/url/*`) | Zero warnings in CI |
| 1.3 | Manual smoke | • Open GUI → crawl 5 random URLs<br>• Verify no 500s | Sign‑off comment in `currentTask.md` |

---

## 2  Test‑Coverage Expansion   *(Iteration 1 – RED)*

Task‑ID | Area | Failing Test to Add | Edge Cases
------- | ---- | ------------------- | ----------
2.1 | Security | `tests/test_url_security_extra.py` | • URL‐encoded traversal (%2e%2e/)<br>• Mixed case `<ScRiPt>`<br>• Null‑byte mid‑segment (`a%00b`) |
2.2 | Normalization | `tests/test_url_normalization_idn.py` | • CJK IDNs<br>• Punycode double‑encode guard |
2.3 | Parsing | `tests/test_url_parsing_windows.py` | Back‑slash paths (`..\\folder`) |
2.4 | Classification | `tests/test_url_classification_subdomain.py` | `images.a.com` vs `a.com` → INTERNAL_SUBDOMAIN |

**Exit‑Criteria:** coverage ≥ 95 % for `src/utils/url/*` (use `pytest --cov`).

---

## 3  Green Implementation   *(Iteration 1 – GREEN)*

Refactor / code updates to make the new failing tests pass.

1. Harden `check_url_security` for percent‑encoding & mixed‑case tags   
2. Add hostname re‑encode guard in `normalize_hostname`   
3. Extend `determine_url_type` to return new enum `INTERNAL_SUBDOMAIN` (update `URLType`) 

---

## 4  Performance Optimisation   *(Iteration 2)*

| ID | Activity | Metrics |
|----|----------|---------|
| 4.1 | Benchmark 1 M synthetic URLs (script in `scripts/benchmark_url_handling.py`) | ⟨ 50 µs / URL |
| 4.2 | Memoise expensive Public‑Suffix look‑ups (`tldextract`) using `lru_cache` | 20 % speed‑up |
| 4.3 | Profile regex hot‑spots with `cProfile` → refactor if pattern dominates > 5 % | Document in `/docs/perf_report.md` |

---

## 5  Advanced Features   *(Iteration 3)*

### 5.1  Fragment Handling  
- [ ] Add `fragment` property to `URLInfo` (🔴 test first).  
- [ ] Decide normalisation rule: keep vs strip vs configurable.

### 5.2  Canonicalisation RFC 3986  
- [ ] Merge consecutive slashes  
- [ ] Percent‑decode unreserved chars  
- [ ] Order query parameters  

### 5.3  Reputation / Block‑lists  
- [ ] Integrate optional `py‑dnsbl` to flag malicious domains.  
- [ ] Async look‑up with caching layer.

---

## 6  Integration Tasks

Component | Action
----------|-------
`LinkProcessor` | Replace legacy parsing logic with `URLInfo`; update unit tests
`BackendSelector` | Remove fallback to deprecated `URLProcessor`
`Crawler` | Add `max_url_count_per_domain` using `URLInfo.netloc` as key
`QualityChecker` | Score boost for internal links (use `URLType`)  

---

## 7  Documentation & DX

- Update **API docs** (`docs/url_handling.md`) with examples for each helper module.  
- Publish **how‑to** notebook in `examples/url_handling_demo.py`.  
- Add **architecture diagram** (Mermaid) in `docs/url_handling_migration.md`.  
- Append all finished subtasks to `projectRoadmap.md > Completed Tasks`.

---

## 8  Future Enhancements (Back‑log)

Priority | Idea
---------|-----
P1 | Plug‑in pattern for custom security rules (callback registry)
P2 | Switch to `pydantic` models for structured URL serialization
P3 | WASM build for fast client‑side validation in the GUI
P4 | Streaming validation of large link‑lists (async generator API)

---

## 9  Milestone Check‑list

- [ ] **Iter 0:** Regression green  
- [ ] **Iter 1:** Coverage ≥ 95 %, new enum delivered  
- [ ] **Iter 2:** Mean latency ⟨ 50 µs / URL  
- [ ] **Iter 3:** Canonicalisation options & fragment support  
- [ ] Docs, examples, and roadmap updated  

---

## Maintainer Notes

* All new code paths **must** include type hints and docstrings.  
* Keep imports dependency‑light inside `src/utils/url/*` to avoid cycles.  
* Use **semantic‑commit** messages (`feat(url): add fragment property`).  
* Ping `@core-reviewers` on every PR touching security rules.