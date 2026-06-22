## Context

The `DictionaryGenerator` class in `backend/core/dict_generator.py` is responsible for producing the keyword mappings used by the Aho-Corasick algorithm during the data cleaning phase. Currently, the `extract_keywords_ai` function is flawed. It calculates scores incorrectly, uses a harsh purity threshold, and improperly prevents overlapping keywords. As a result, the generated dictionaries are missing critical multi-word keywords (e.g., "đèn led âm trần"), which causes downstream classification logic to perform suboptimally.

## Goals / Non-Goals

**Goals:**
- Update `extract_keywords_ai` to follow the exact scoring algorithm defined in `SYSTEM_DOCUMENTATION.md`.
- Ensure multi-word, high-value keywords are correctly identified and scored.
- Update overlap prevention so that shorter overlapping substrings are discarded in favor of longer, more specific n-grams, rather than the other way around.
- Lower the purity threshold to 0.05 (5%) to preserve valid but less frequent domain-specific keywords.
- Update token validation logic so that complete n-grams can be evaluated correctly even if their first word is numeric.

**Non-Goals:**
- Completely rewriting the overall dictionary generation architecture.
- Adjusting the Aho-Corasick matching logic itself (this is downstream and assumed to be working correctly).

## Decisions

**1. Scoring Function Implementation:**
- Calculate base score as `words_count = len(n.split())`.
- Add a 20 point bonus if `n` contains any of the predefined High Value keywords.
- Apply a 0.5 multiplier to the final score if `words_count == 1`.
- Rationale: This exactly aligns with the business logic detailed in the system documentation.

**2. Overlap Prevention:**
- Sort the generated candidate list by `(words_count, score)` descending.
- When traversing candidates, if a candidate is a substring of an already selected top keyword, skip it.
- If a candidate contains a shorter substring that is already in the top keywords, remove the shorter substring and add the new, longer candidate.
- Rationale: The Aho-Corasick matcher relies on masking (consuming) matched strings. We must provide the longest, most specific strings possible so they match before shorter components.

**3. Token Validation:**
- Stop using `_is_valid_cluster_token(n)` directly on the full n-gram string in `extract_keywords_ai`.
- Rationale: The validation uses regular expressions meant for single words and rejects strings like "10w âm trần". We will ensure `tokenize_vi` handles invalid tokens at the word level, and n-grams formed from valid words will automatically be considered valid.

## Risks / Trade-offs

- **Risk:** Lowering the purity threshold to 0.05 might introduce noisier, less distinct keywords.
  - **Mitigation:** The overlap prevention logic prioritizing longer n-grams should help absorb noise. If false positives rise in downstream matching, the threshold can be slightly tuned to 0.10.
- **Risk:** High-value keywords might dominate results in small clusters.
  - **Mitigation:** The Aho-Corasick algorithm works by matching the longest string anyway. A high-value keyword string matching accurately is the desired behavior for the pipeline.
