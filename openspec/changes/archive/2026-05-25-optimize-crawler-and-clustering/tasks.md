## 1. Crawler Enhancements

- [x] 1.1 Enhance `crawl_hs_code` in `backend/core/crawler.py` to fetch Heading level description (4 digits) and use it as `dong_sp`.
- [x] 1.2 Update regex and cleanup on crawled descriptions to keep them clean.

## 2. Text Preprocessing & Clustering Optimization

- [x] 2.1 Update `clean_text` in `backend/core/dict_generator.py` with strict regex patterns to strip model codes and sizes.
- [x] 2.2 Adjust DBSCAN parameters (`eps=0.70` and `min_samples=8`) in `generate_draft_taxonomy`.

## 3. Verification

- [x] 3.1 Verify dictionary draft generation output via `test_step1.py` or by testing Step 1 in the running app.
