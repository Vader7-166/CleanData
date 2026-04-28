## Why

The current Hybrid Prediction pipeline is suffering from severe performance bottlenecks (e.g., taking 2-4 minutes to process just 500 rows). This happens because the AI model is run iteratively on a row-by-row basis (batch size = 1) instead of batch processing, and the dictionary mapping uses dynamic regex search inside nested loops. This change is needed now to make the application usable for large datasets (e.g., 30k rows).

## What Changes

- Modify the classification logic to run the dictionary scoring (`dictv3`) globally across the entire dataset FIRST.
- Filter out rows that are successfully classified by the dictionary (score >= threshold).
- Group the remaining rows (those that need AI fallback) and pass them to the PhoBERT model in optimized batches (e.g., batch size 16 or 32) instead of row-by-row.
- Pre-compile regular expressions (`re.compile`) during the dictionary loading phase to eliminate repetitive compilation overhead.

## Capabilities

### New Capabilities

### Modified Capabilities
- `dictionary-filtering`: The dictionary logic is now separated to act as a pre-filter pass on the entire dataset rather than row-by-row interwoven with the AI call. The AI fallback now accepts batches of data instead of single rows.

## Impact

- **Backend (`core/data_cleaner.py`)**: The `predict_hybrid`, `predict_with_threshold`, and `process_async` methods will be heavily refactored. The AI inference will be extracted into a batch-processing function. Dictionary loading will be updated to pre-compile regex objects.
- **Performance**: Significant reduction in prediction time.
