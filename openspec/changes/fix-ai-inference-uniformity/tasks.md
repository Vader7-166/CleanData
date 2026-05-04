## 1. Diagnostics and Reproduction

- [ ] 1.1 Create `debug_inference.py` script to load the model and run inference on manual inputs
- [ ] 1.2 Reproduce the uniform output issue using the script and various input strings
- [ ] 1.3 Log `input_for_ai` samples from a real processing run in `DataCleaner.process_async`

## 2. Preprocessing Fixes

- [ ] 2.1 Verify `input_for_ai` generation logic in `DataCleaner.process_async` handles missing values correctly
- [ ] 2.2 Ensure `clean_text_for_dict` doesn't over-sanitize strings into identical outputs

## 3. Inference Logic Fixes

- [ ] 3.1 Audit `predict_ai_batch` for incorrect indexing or vector-to-scalar conversions
- [ ] 3.2 Verify that `torch.max` is correctly reducing along the class dimension for each batch item
- [ ] 3.3 Ensure the `label_encoder` mapping happens individually for each result in the batch

## 4. Validation

- [ ] 4.1 Run the `debug_inference.py` script again to confirm varied outputs for varied inputs
- [ ] 4.2 Perform a full pipeline test with a dataset known to trigger AI fallback
- [ ] 4.3 Verify that confidence scores and labels are diverse and appropriate
