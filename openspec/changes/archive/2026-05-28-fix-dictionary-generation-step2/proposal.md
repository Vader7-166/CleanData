## Why

The current implementation of Step 2 in the Dictionary Generator (keyword extraction) produces results that are inconsistent with the original `Create_Dictionary/keyword_extractor.py` logic. Specifically, it calculates keyword "purity" globally across the entire dictionary instead of locally within each HS Code group, leading to less accurate and generic keywords for diverse datasets.

## What Changes

- Refactor `DictionaryGenerator.extract_keywords_for_taxonomy` to iterate over groups by HS Code.
- Update `DictionaryGenerator.extract_keywords_ai` to calculate ngram frequencies relative to the current HS Code context (local purity).
- Improve product-to-category matching by ensuring all products from merged clusters are considered for keyword extraction.
- Ensure consistent tokenization and stopword filtering between the backend and the original research scripts.

## Capabilities

### New Capabilities
- None

### Modified Capabilities
- `dictionary-generation-integration`: Update the keyword extraction logic to prioritize local purity within HS codes for better accuracy.

## Impact

- `backend/core/dict_generator.py`: Major logic updates to `extract_keywords_for_taxonomy` and `extract_keywords_ai`.
- `backend/main.py`: Minor adjustment to how Step 2 is called if needed (async handling).
- Accuracy of generated dictionaries will significantly improve, matching the performance of the standalone research script.
