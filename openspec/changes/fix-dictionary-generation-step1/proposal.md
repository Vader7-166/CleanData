## Why

Step 1 of the Dictionary Generation pipeline (Draft Generation) is currently producing an excessive number of clusters (e.g., over 1000 groups for a single LED product dataset). This is because the clustering algorithm defaults to `eps=0.45` and `min_samples=2`, whereas the system documentation mandates `eps=0.65` and `min_samples=5`. Additionally, the LLM labeling process frequently fails or returns invalid dictionary objects due to an ambiguous prompt, which leads to `TypeError` exceptions during the detection of NC/LK types, falling back to garbage Lớp 2 outputs.

## What Changes

- Update `eps` and `min_samples` default values in `DictionaryGenerator.generate_draft_taxonomy` to `0.65` and `5` respectively, aligning with the `SYSTEM_DOCUMENTATION.md`.
- Fix the LLM prompt in `label_clusters_llm` to match the robust prompt used in `Create_Dictionary/llm_labeler.py`, preventing nested JSON responses.
- Implement robust JSON parsing in `label_clusters_llm` to handle cases where the LLM still returns nested dictionaries (e.g., `{"1": {"Tên": "Đèn LED"}}`).
- Add logging to track the number of clusters sent to the LLM and the success/failure rate of LLM labeling.

## Capabilities

### New Capabilities
- None

### Modified Capabilities
- `llm-cluster-labeling`: Fix LLM prompt and parsing to ensure robust JSON decoding and prevent nested object returns.

## Impact

- `backend/core/dict_generator.py`: Modifications to `generate_draft_taxonomy`, `label_clusters_llm`, and `detect_type` error handling.
- Step 1 will generate significantly fewer, more meaningful clusters, greatly reducing the manual review workload.
- LLM labeling will successfully assign names to clusters instead of crashing or falling back to raw TF-IDF names.
