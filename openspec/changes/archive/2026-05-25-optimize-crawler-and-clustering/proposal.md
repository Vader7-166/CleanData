## Why

The current dictionary generation pipeline produces cluttered and noisy Level 2 categories with meaningless combined keywords. This happens because the crawler fallback is hardcoded to only 5 product lines, and the text preprocessing does not filter out alphanumeric noise (such as model numbers, sizes, and measurement units) from the customs descriptions.

## What Changes

- **Double-Request HS Code Crawling**: Enhance the online crawler to crawl the 4-digit Heading description as the dynamically inferred Product Line (`dong_sp`) when encountering an unknown HS code, alongside the 8-digit Lớp 1 description.
- **Advanced Text Preprocessing**: Enhance `clean_text` in `dict_generator.py` with strict regex rules to strip model numbers, size values, and measuring units before vectorization.
- **DBSCAN Parameter Tuning**: Adjust DBSCAN parameters (`eps` to `0.70` and `min_samples` to `8`) to reduce trivial groups, pushing miscellaneous items into the outlier (`-1`) group.

## Capabilities

### New Capabilities
*None*

### Modified Capabilities
*None*

## Impact

- `backend/core/crawler.py` (crawling mechanism and `infer_dong_sp` logic)
- `backend/core/dict_generator.py` (text preprocessing and DBSCAN tuning)
