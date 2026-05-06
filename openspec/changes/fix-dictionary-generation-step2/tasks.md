## 1. Backend: Core Logic Refactoring

- [x] 1.1 Refactor `DictionaryGenerator.extract_keywords_for_taxonomy` to iterate over groups by HS Code.
- [x] 1.2 Update `DictionaryGenerator.extract_keywords_ai` to accept local group frequencies and global frequencies relative to the context (HS Code).
- [x] 1.3 Ensure `c_map` (cluster mapping) correctly handles `Cluster_ID` types (string vs float vs int) from Excel.
- [x] 1.4 Standardize the fallback regex matching to use the same tokenization as the primary mapping.

## 2. Backend: Integration & API

- [x] 2.1 Verify `backend/main.py` correctly passes the `raw_with_cluster_df` to the generator.
- [x] 2.2 Add logging to Step 2 to monitor how many groups are matched via `Cluster_ID` vs Fallback.

## 3. Verification

- [x] 3.1 Run a test with a sample draft containing multiple HS codes.
- [x] 3.2 Compare the generated keywords with the output of the original `keyword_extractor.py` for the same input.
- [x] 3.3 Validate that keywords are distinguishing within each HS code group.
