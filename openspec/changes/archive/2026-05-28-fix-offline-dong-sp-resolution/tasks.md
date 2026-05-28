## 1. Backend Implementation

- [x] 1.1 Import `hs_customs_cache` inside `infer_dong_sp` in `backend/core/crawler.py` and implement cache lookup.
- [x] 1.2 Apply `clean_dong_sp_description` to the resolved description from cache before returning it.

## 2. Verification

- [x] 2.1 Restart backend Docker container to apply changes.
- [x] 2.2 Verify resolution of `01012100` and `01013090` returns the clean product line from cache.
