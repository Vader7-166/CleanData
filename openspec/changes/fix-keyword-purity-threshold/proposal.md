## Why

Currently, the TF-IDF keyword extraction algorithm (`extract_keywords_ai`) in the dictionary generator forces the extraction of up to 12 keywords (`top_n=12`) for each category. If a category's product descriptions lack diversity, the algorithm will pick low-purity, generic n-grams (e.g., brand names like "Rạng Đông", or generic parts like "đèn đi ốt" with purity < 1%) just to fulfill the quota. During the data cleaning process, this causes severe misclassifications (e.g., all "Rạng Đông" products being incorrectly grouped into `led panel tròn`). Adding a strict Purity threshold prevents generic "garbage" keywords from polluting the dictionary.

## What Changes

- Add a minimum purity threshold check (e.g., `p >= 0.2` or 20%) in `extract_keywords_ai`.
- Prevent low-purity n-grams from being added to the candidate list, effectively allowing categories to return fewer than 12 keywords if only a few are genuinely distinctive.

## Capabilities

### New Capabilities
- `keyword-purity-filtering`: The ability to filter out low-purity keywords during TF-IDF extraction to ensure dictionary accuracy.

### Modified Capabilities
- `<existing-name>`: None

## Impact

- **Affected Code**: `backend/core/dict_generator.py` (specifically `extract_keywords_ai`).
- **Impact**: The generated dictionaries (`DICT_HQ.csv`, etc.) will have fewer but much higher-quality keywords. This will significantly boost the accuracy of the `DictionaryMatcher` and eliminate the "overfitting" misclassification anomalies observed in the cleaned data.
