## Why

The current output result file has a column order that does not match the expected `sample.csv` format, making it difficult for users or downstream systems to process the data efficiently. We need to reorder the columns to align with `sample.csv` and ensure the internal metadata columns ("trạng thái" / status and "độ tự tin" / confidence) are positioned at the very end of the file.

## What Changes

- Update the output generation logic to reorder columns according to the headers in `sample.csv`.
- Force the "Trạng thái" (Status) and "Độ tự tin" (Confidence) columns to always be the last two columns in the exported result file.

## Capabilities

### New Capabilities
- `result-formatting`: Defines the column ordering rules for the final output files based on a reference sample file.

### Modified Capabilities

## Impact

- Data export modules/functions (likely in `backend/core/data_cleaner.py` or `extracted_pipeline.py`).
- Downstream users relying on the exact column order of the output files.