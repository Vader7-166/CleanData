## 1. Backend Optimization Preparation

- [x] 1.1 Update the `DataCleaner._load_dict` function to pre-compile the keyword regular expressions (`re.compile`) and store them in the `dict_mapping` list.

## 2. Refactor Prediction Logic

- [x] 2.1 Refactor the `predict_hybrid` function to only perform the Dictionary scoring (using the pre-compiled regex). It should no longer call the AI model directly as a fallback.
- [x] 2.2 Create a new `predict_ai_batch` method in `DataCleaner` that accepts a batch (list or Series) of texts, tokenizes them, runs `model(**inputs)`, and decodes the predictions.

## 3. Update Pipeline Flow

- [x] 3.1 Update `DataCleaner.process_async` to first apply the updated `predict_hybrid` (Dictionary pass) on all rows.
- [x] 3.2 Filter out the rows that failed the Dictionary pass (e.g., status is "Cần kiểm tra" or score < threshold).
- [x] 3.3 Pass the filtered subset of texts to the new `predict_ai_batch` method in chunks (e.g., chunk size 32 or 64).
- [x] 3.4 Merge the batched AI predictions back into the main DataFrame results.

## 4. UI & Progress Logging

- [x] 4.1 Update the `progress_callback` messages inside `process_async` to reflect the new decoupled passes (e.g., "Dictionary Matching...", "AI Inference (Batch X/Y)...").

## 5. Testing & Validation

- [x] 5.1 Test the new pipeline with a large dataset (or a dummy subset) to ensure the total processing time is significantly reduced and no data is lost during the merge.