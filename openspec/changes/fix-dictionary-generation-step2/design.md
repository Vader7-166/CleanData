## Context

The `DictionaryGenerator` class in the backend was ported from a research repository to handle dictionary generation through a web API. While the clustering (Step 1) works well, the keyword extraction (Step 2) is currently calculating keyword purity globally across all groups in the uploaded draft. This differs from the original research logic where purity is calculated relative to groups within the same HS code, leading to generic or inaccurate keywords when the dataset spans multiple HS categories.

## Goals / Non-Goals

**Goals:**
- Align `extract_keywords_for_taxonomy` with the per-HS-code logic of `keyword_extractor.py`.
- Ensure keyword "purity" is calculated locally within each HS code group.
- Maintain support for both `Cluster_ID` based matching and regex fallback matching.

**Non-Goals:**
- Changing the clustering algorithm (Step 1).
- Modifying the frontend UI flow.
- Changing the final dictionary CSV format.

## Decisions

### HS-Code Scoping in Keyword Extraction
- **Decision:** Wrap the call to `extract_keywords_ai` inside a loop that iterates over unique HS codes in the draft taxonomy.
- **Rationale:** Purity scores (Local Frequency / Global Frequency) are only meaningful when the "Global Frequency" is defined within the relevant competitive set—which in this project is the set of categories sharing the same HS code.
- **Alternative:** Calculate a "Global-Global" frequency once and use it everywhere. This was rejected because it penalizes common words (like "nhựa", "thủy tinh") that are highly distinguishing within their specific HS code contexts.

### Data Aggregation for Keyword Extraction
- **Decision:** Before extracting keywords, group all products from the raw data by `(HS_Code, Cluster_ID)` into a mapping.
- **Rationale:** This ensures that we can quickly retrieve the exact set of products belonging to a cluster suggested in Step 1.
- **Refinement:** If a user manually merges rows in the draft (by giving them the same Lớp 2), the system should ideally consider all associated products. However, to keep it simple and consistent with the original script, we will continue to use the primary `Cluster_ID` listed in each row.

## Risks / Trade-offs

- **[Risk]** → Performance might slightly decrease due to repeated Counter operations per HS code.
- **[Mitigation]** → The number of groups per HS code is typically small (tens to hundreds), so the overhead of multiple `extract_keywords_ai` calls is negligible compared to the IO of reading Excel files.
- **[Trade-off]** → Using local purity means that a word could potentially be a keyword for two different categories in two different HS codes. This is acceptable as the dictionary matcher typically filters by HS code first.
