## Context

The Draft Taxonomy Generation (Step 1) relies on DBSCAN clustering followed by an LLM-based labeling step to provide human-readable group names (Lớp 2). Currently, for complex datasets like LED products (HS 8539), the system generates over 1000 clusters. This is driven by overly sensitive default clustering parameters (`eps=0.45`, `min_samples=2`), which contradict the standard documentation (`eps=0.65`, `min_samples=5`). 
Furthermore, when hitting the LLM (Groq) with a high volume of clusters, the ambiguous JSON prompt sometimes causes the model to return nested JSON objects. The backend fails to parse this correctly, resulting in `TypeError` crashes during the downstream `detect_type` function, effectively rendering the Lớp 2 column useless.

## Goals / Non-Goals

**Goals:**
- Reduce the volume of clusters by correcting the `eps` and `min_samples` defaults.
- Prevent crashes by robustly handling and parsing the JSON output from Groq.
- Improve the prompt provided to Groq to match the one successfully used in `llm_labeler.py`.
- Add debugging logs to track the LLM labeling progress.

**Non-Goals:**
- Completely rewriting the clustering algorithm.
- Switching to a different LLM provider.

## Decisions

### 1. Correcting DBSCAN Parameters
- **Decision:** Change default parameters in `DictionaryGenerator.generate_draft_taxonomy` to `eps=0.65` and `min_samples=5`.
- **Rationale:** Aligns with the project's documented standard, drastically reducing the number of micro-clusters and bringing the manual review effort down to a manageable level (e.g., from ~1000 to ~250 for LED products).

### 2. LLM Prompt Alignment
- **Decision:** Replace the short prompt in `dict_generator.py` with the detailed instruction set from `llm_labeler.py`.
- **Rationale:** The prompt in `llm_labeler.py` explicitly instructs the LLM not to include codes or brands and specifies the exact JSON format `{"0": "Tên danh mục 0"}`, which significantly reduces hallucinations and structural errors.

### 3. Robust JSON Parsing
- **Decision:** Add type-checking logic when extracting values from the LLM's JSON response: `if isinstance(val, dict): val = val.get("id") or val.get("Tên") or list(val.values())[0]`.
- **Rationale:** Even with a good prompt, LLMs can deviate. Robust extraction ensures that if Groq returns `{"1": {"Tên": "Đèn LED"}}` instead of `{"1": "Đèn LED"}`, the system extracts `"Đèn LED"` instead of passing a dictionary to the string manipulation functions.

## Risks / Trade-offs

- **[Risk]** Larger `eps` could group slightly dissimilar items together.
- **Mitigation:** Reviewers can easily spot and split these during the manual review phase, which is much faster than manually renaming 1000+ separate micro-clusters.
