## 1. Update DictionaryMatcher Core

- [x] 1.1 In `backend/core/dictionary_matcher.py`, update `_load_dict()` to store `ma_hs` directly in the Aho-Corasick payload: `(mapping_idx, len(kw), score, kw, ma_hs)`.
- [x] 1.2 Update `predict` signature to `def predict(self, text, hs_code=None):`.
- [x] 1.3 In `predict`, extract the 4-digit prefix of the input `hs_code` (if provided).
- [x] 1.4 In the Aho-Corasick match iteration loop, extract the entry's `ma_hs` from the payload. If input `hs_code` is valid and the 4-digit prefixes do NOT match, divide the score by 10 (or discard it).
- [x] 1.5 Handle the fallback case where `hs_code` is None, NaN, or empty by treating it as a valid match without penalties.

## 2. Update Downstream Callers

- [x] 2.1 In `backend/core/worker.py`, update the dictionary matching logic to pass the `Mã HS` column to `matcher.predict`. This likely requires changing `input_for_ai.apply(matcher.predict)` to apply across the DataFrame rows instead of just the text series.
- [x] 2.2 In `backend/core/data_cleaner.py`, update any calls to `predict_dictionary` to ensure the `Mã HS` is being retrieved from the row data and passed down to `matcher.predict`.
- [x] 2.3 Verify that the `cleaned_merged_upload (4).csv` output reflects the changes.

## 3. Verification

- [x] 3.1 Run tests to verify that products like "đèn led năng lượng mặt trời" with HS code `94054990` do NOT get incorrectly matched to "đèn côn trùng" (which originated from `94054190` or `8539...`).
- [x] 3.2 Ensure products with NO HS code still get matched based purely on text substrings.
