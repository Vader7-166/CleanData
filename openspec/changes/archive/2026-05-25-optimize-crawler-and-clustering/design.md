## Context

The current DBSCAN clustering and labeling generate messy results (meaningless keywords and scattered small groups) because the crawler lacks dynamically fetched product lines (`dong_sp`) and the vectorization includes too much alphanumeric noise.

## Goals / Non-Goals

**Goals:**
- Automatically crawler-retrieve both Lớp 1 (8-digit) and Dòng sản phẩm (4-digit) descriptions for unknown HS codes.
- Preprocess product descriptions to remove models, quantities, and other alphanumeric tokens.
- Restructure DBSCAN params (`eps` and `min_samples`) for more coherent group clustering.

**Non-Goals:**
- Replacing DBSCAN with other clustering models (e.g., K-Means).
- Re-architecting the database schema or the UI structure.

## Decisions

### Decision 1: Multi-Level HS Code Crawling
- **Approach**: When crawling an unknown 8-digit HS code, also query the 4-digit prefix Heading description. Use this Heading description as the dynamically crawled Dòng sản phẩm (`dong_sp`), and the 8-digit description as Lớp 1.
- **Alternative**: Asking the user to manually enter `dong_sp` for every newly discovered HS code (increases friction, rejected).

### Decision 2: Strict Text Preprocessing Regex
- **Approach**: In `dict_generator.py -> clean_text()`, add regex filters to strip:
  - Alphanumeric strings representing model numbers (e.g., `RS378B`, `15W`, `12oz`).
  - Standalone units (`pcs`, `set`, `cái`, `chiếc`, `m`, `cm`, `mm`, `kg`, `v`, `w`).
  - Leading/trailing special characters and common brand tokens.
- **Alternative**: Using standard NLTK/pyvi stopword removal alone (insufficient for numeric model noise).

### Decision 3: DBSCAN Tuning
- **Approach**: Increase `eps` from `0.65` to `0.70` and increase `min_samples` from `5` to `8`.
- **Alternative**: Leave as is (leads to tiny, noisy clusters).

## Risks / Trade-offs

- **Risk**: Multiple HTTP crawl requests for 4-digit and 8-digit codes might increase latency or get rate-limited.
  - *Mitigation*: Fall back to default DB tax prefixes if the HTTP crawl fails, and reuse cached values.
- **Risk**: Strict regex might remove essential descriptive details if they are formatted like models.
  - *Mitigation*: Ensure the regex only targets tokens with numbers mixed with letters, rather than pure product keywords.
