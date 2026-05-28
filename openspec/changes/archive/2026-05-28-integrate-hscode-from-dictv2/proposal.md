## Why

The current dictionary-based classification only maps product keywords to categories (Dòng SP, Loại, Lớp 1, Lớp 2) but ignores the HS CODE (Mã HS) available in improved dictionary versions like `dictv2.csv`. Incorporating HS CODE into the dictionary matching process will provide more accurate and complete labeling, ensuring consistency between product descriptions and their official customs classification codes.

## What Changes

- Update dictionary loading logic to detect and extract the `Mã HS` (HS CODE) column from dictionary files.
- Modify the dictionary matching prediction to include `Mã HS` in the result payload when a match is found.
- Update the data cleaning pipeline to assign the HS CODE from the dictionary to the processed records, complementing or refining the raw data's HS Code.
- Update `DataCleaner` to utilize `dictv2.csv` as the reference dictionary to leverage its additional metadata.

## Capabilities

### New Capabilities
- None.

### Modified Capabilities
- `dictionary-filtering`: Update requirement to include HS CODE extraction and mapping during the dictionary matching phase.

## Impact

- **Backend**: `backend/core/data_cleaner.py` will require updates to `_load_dict`, `predict_dictionary`, and `process_async` to handle the additional HS CODE field.
- **Data Pipeline**: The final output dataset will have the `Mã HS` column enriched by dictionary-matched values, improving data quality for classification.
- **Storage**: `dataset/dictv2.csv` becomes the primary reference for the hybrid classification system.
