## Why

When resolving HS codes offline using the `HSCustomsReference` cache, the system falls back to setting the product line (`dong_sp`) to `SP {prefix4}` (e.g., `SP 0101`) for any prefix not present in the hardcoded `DONG_SP_FALLBACK` mapping. This results in unfriendly and uninformative product line labels since the correct descriptive heading (e.g., `Ngựa, lừa, la sống`) is already available in the offline tariff database.

## What Changes

- Modify `infer_dong_sp` in `backend/core/crawler.py` to first look up the 4-digit prefix in the loaded in-memory `hs_customs_cache`.
- Clean the retrieved 4-digit heading description (e.g., `Ngựa, lừa, la sống` -> `SP NGỰA`) using `clean_dong_sp_description`.
- Fall back to the existing `DONG_SP_FALLBACK` map and the `SP {prefix4}` pattern only if the prefix description is not present in the cache.

## Capabilities

### New Capabilities
<!-- None -->

### Modified Capabilities
- `hs-taxonomy-lookup`: Improve the resolution of product lines (`dong_sp`) from offline cache lookup by utilizing 4-digit heading descriptions from `HSCustomsReference`.

## Impact

- `backend/core/crawler.py`: Modifies the `infer_dong_sp` helper function to lookup the prefix description from the memory cache.
- `backend/main.py`: The `check_hs_codes` endpoint will now return descriptive product lines (e.g., `SP NGỰA` instead of `SP 0101`).
