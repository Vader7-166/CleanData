## Context

The current hybrid classification pipeline utilizes a dictionary matching pass (Pass 1) followed by an AI model pass (Pass 2). The dictionary mapping currently only covers four categorical levels (Dòng SP, Loại, Lớp 1, Lớp 2). However, newer dictionary versions like `dictv2.csv` contain the `Mã HS` (HS CODE) field, which is essential for accurate customs data processing. Currently, the `Mã HS` column in the output is derived solely from the raw input and is not refined by the dictionary matching process.

## Goals / Non-Goals

**Goals:**
- Update `DataCleaner` to load and store `Mã HS` from dictionary files.
- Extend the dictionary matching result to include the `Mã HS` value.
- Ensure the data cleaning pipeline updates the `Mã HS` column in the final result with values from high-confidence dictionary matches.
- Set `dictv2.csv` as the default dictionary file for the pipeline.

**Non-Goals:**
- Implementing AI-based HS CODE prediction (AI remains focused on the 4 categorical levels).
- Processing other auxiliary columns like `Cluster_ID` at this stage.

## Decisions

### 1. Dictionary Internal Schema Expansion
- **Decision**: Update the `dict_mapping` structure to include the `Mã HS` value.
- **Rationale**: The `label_str` currently used to return results will be expanded from 4 segments to 5 segments: `f"{d_sp} | {loai} | {lop_1} | {lop_2} | {ma_hs}"`.
- **Alternatives**: Returning a separate column for HS Code from `predict_dictionary`. Rejected as it would require significant refactoring of the async processing chunks and column merging logic.

### 2. Default Dictionary Update
- **Decision**: Change the default `dict_path` in `DataCleaner` and `get_cleaner` from `dictv3.csv` to `dictv2.csv`.
- **Rationale**: `dictv2.csv` provides the necessary HS CODE mapping required for this enhancement.

### 3. Pipeline Assignment Logic
- **Decision**: Update `split_and_assign` in `process_async` to handle 5 segments instead of 4.
- **Rationale**: This allows for a clean, centralized assignment of all dictionary-derived fields, including the refined HS CODE.

## Risks / Trade-offs

- **[Risk]**: Inconsistent dictionary formats (e.g., missing `Mã HS` column). → **Mitigation**: The loader will use `.get()` with a default value of `'không_có'` to maintain backward compatibility with older dictionary formats like `dictv3.csv`.
- **[Risk]**: Overwriting existing HS Codes in raw data. → **Mitigation**: This is a desired behavior for high-confidence dictionary matches (Pass 1), as the dictionary is a curated reference.
