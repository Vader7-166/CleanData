## Why

The AI classification pass (Pass 2) is currently producing identical results (same label and confidence score) across different input rows. This indicates a failure in the inference pipeline, possibly due to input normalization issues, incorrect batch processing, or model loading inconsistencies. Fixing this is critical for the system's reliability when dictionary matches are unavailable.

## What Changes

- **Inference Diagnostic Tool**: Create a script to run inference on sample inputs and log internal tensor shapes and outputs.
- **Input Normalization Fix**: Review and correct the `input_for_ai` generation logic to ensure varied inputs are correctly formatted for the tokenizer.
- **Batch Processing Correction**: Audit the `predict_ai_batch` method to ensure that each sample in the batch is processed independently and correctly mapped back to its index.
- **Model Verification**: Validate that the PhoBERT model and label encoder are correctly loaded and that the output logits correspond to the expected classes.

## Capabilities

### New Capabilities
- `ai-inference-diagnostics`: Implementation of tools to debug and verify AI model outputs during development and production.

### Modified Capabilities
- `dictionary-filtering`: Update the AI fallback requirement to ensure high-fidelity predictions when dictionary scores are low.
- `multithreaded-processing`: Ensure the concurrent AI batch processing logic maintains data integrity and sample independence.

## Impact

- `backend/core/data_cleaner.py`: Significant updates to inference logic and preprocessing.
- `backend/main.py`: Possible changes to how the model is initialized.
- Performance: Correcting batch processing might have slight impacts on throughput but will ensure correctness.
