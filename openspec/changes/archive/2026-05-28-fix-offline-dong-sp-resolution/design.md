## Context

When looking up HS codes offline, the system matches the code in the `hs_customs_cache` loaded in memory on startup. It resolves the product line (`dong_sp`) by calling `infer_dong_sp(hs_code)` which falls back to `SP {prefix4}` (e.g. `SP 0101`) for unknown categories. This occurs because `infer_dong_sp` only uses a hardcoded map of project-focused product lines. However, we have a complete tariff database loaded, meaning the descriptive heading (e.g., `0101` -> `Ngựa, lừa, la sống`) is already in our cache.

## Goals / Non-Goals

**Goals:**
- Dynamically resolve the product line (`dong_sp`) from the description of its 4-digit prefix in `hs_customs_cache`.
- Clean the retrieved prefix description using the existing cleaning function `clean_dong_sp_description`.
- Maintain existing fallbacks (`DONG_SP_FALLBACK` map and `SP {prefix4}`) if the prefix is not in the cache or has no description.

**Non-Goals:**
- Modify the database schema.
- Implement online crawling changes.

## Decisions

### Decision: Check memory cache inside `infer_dong_sp`
We will import `hs_customs_cache` dynamically inside the `infer_dong_sp` function (located in `backend/core/crawler.py`) to lookup the 4-digit prefix description.
- *Rationale:* Importing inside the function avoids circular dependency issues with `backend.main`. It ensures any caller of `infer_dong_sp` (both offline cache lookup and crawler fallbacks) automatically gets the improved descriptive name.

## Risks / Trade-offs

- *Risk:* Circular imports if we are not careful with importing `hs_customs_cache` from `backend.main`.
  *Mitigation:* Import `hs_customs_cache` locally inside the `infer_dong_sp` function only, wrapped in a `try-except` block to avoid startup failures.
