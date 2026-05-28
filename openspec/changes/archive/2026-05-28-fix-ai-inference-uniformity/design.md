## Context

The current AI fallback logic in `DataCleaner.process_async` collects rows that fail the dictionary threshold and sends them to `predict_ai_batch`. Reports indicate that all rows, regardless of content, receive the same prediction and confidence score. This suggests the input to the model might be static or the inference loop is incorrectly accumulating/overwriting results.

## Goals / Non-Goals

**Goals:**
- Identify the root cause of uniform AI outputs.
- Ensure `predict_ai_batch` produces unique predictions for unique inputs.
- Implement a logging mechanism to verify input variability before inference.
- Optimize the tokenizer usage to handle batch inputs efficiently.

**Non-Goals:**
- Re-training the PhoBERT model.
- Changing the dictionary matching logic (unless it incorrectly feeds the AI).
- Modifying the frontend UI.

## Decisions

### 1. Diagnostic Logging
- **Decision**: Add verbose logging in `process_async` and `predict_ai_batch` to print the first 5 `input_for_ai` strings being sent to inference.
- **Rationale**: Quickly verify if the problem is in preprocessing (static strings) or in inference (static outputs).

### 2. Input String Reconstruction
- **Decision**: Audit the `input_for_ai` column generation. Ensure that `df_clean['Hãng']`, `df_clean['Công suất']`, and `df_clean['Tên hàng']` are correctly populated for fallback rows.
- **Rationale**: If these columns are empty or contain placeholders, the concatenated string will be identical for all rows.

### 3. Batch Inference Logic Review
- **Decision**: Ensure `self.tokenizer(batch_texts, ...)` is called on the list of unique strings. Verify that `pred_ids` are mapped back to labels using the correct index from the `probabilities` tensor.
- **Rationale**: A common error is using a scalar instead of a vector or incorrectly indexing the batch dimension.

### 4. Label Encoder Verification
- **Decision**: Confirm that `label_encoder.inverse_transform` is used within the loop for each `pred_id` and not just once for the whole batch.

## Risks / Trade-offs

- **[Risk] Sensitive Data in Logs** → Product descriptions might contain sensitive info.
  - **Mitigation**: Log only the first few characters or a hash if needed, but for debugging, local logs of a few samples are acceptable.
- **[Risk] Performance Overheads** → Logging and extra validation can slow down processing.
  - **Mitigation**: Keep diagnostics enabled only for a "debug mode" or limited to a small sample count.
