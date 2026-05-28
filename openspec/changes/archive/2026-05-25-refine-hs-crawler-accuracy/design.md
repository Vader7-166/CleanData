# Design: Refining HS Crawler Accuracy

This design covers prompt enhancements for the DeepSeek LLM fallback and improvements to the fallback regex matching in the public crawler.

## Proposed Changes

### Backend Crawler

#### [MODIFY] [crawler.py](file:///e:/T%C3%80I%20LI%E1%BB%86U%20TH%E1%BB%B0C%20T%E1%BA%ACP/D%E1%BB%B1%20%C3%A1n%20%20L%C3%A0m%20s%E1%BA%A1ch%20v%C3%A0%20chu%E1%BA%A9n%20h%C3%B3a%20d%E1%BB%AF%20li%E1%BB%87u/CleanData/backend/core/crawler.py)

1. **DeepSeek Prompt Tuning**:
   - Instruct the LLM to strictly isolate the 8-digit leaf node description (`industry_name`) from the 4-digit heading level description (`dong_sp_desc`).
   - Add negative constraints and explicit rules:
     - `industry_name` must represent the specific subclass (e.g. `90012000` is "Tấm và bản bằng vật liệu phân cực").
     - Must NOT copy-paste or fall back to the generic group title (e.g. "Thấu kính, lăng kính...") unless the subheading itself has no further refinement.

2. **Regex Parsing Refinement**:
   - In `_crawl_hscode_pro`, change the fallback pattern to look for the full `hs_code` instead of slicing it to the 4-digit prefix `hs_code[:4]`.
   - Pattern to modify:
     ```python
     # Find Vietnamese description near the full code
     pattern = re.compile(
         rf'{re.escape(hs_code)}[.\d]*\s*[-–:]\s*(.{{10,120}})',
         re.IGNORECASE
     )
     ```
