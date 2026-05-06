## 1. Parameters & Configuration

- [x] 1.1 Update `generate_draft_taxonomy` default parameters to `eps=0.65` and `min_samples=5`.

## 2. LLM Labeling Improvements

- [x] 2.1 Update the Groq prompt in `DictionaryGenerator.label_clusters_llm` to match `llm_labeler.py`, instructing it strictly on JSON format and category naming rules.
- [x] 2.2 Add robust parsing logic in `label_clusters_llm` to handle nested dict returns (extracting string values if a dict is returned).
- [x] 2.3 Add logging inside `label_clusters_llm` to report the number of batches and the success/failure of each batch.

## 3. Verification

- [x] 3.1 Run a local test with `8539-NK-Th12.2025.xlsx` to confirm that the number of generated clusters is around 260 instead of 1000+.
- [x] 3.2 Ensure the script does not crash with a `TypeError` during the `detect_type` phase when LLM is enabled.
