## 1. Preparation and Benchmarking

- [x] 1.1 Establish a baseline performance metric using the existing `debug_inference.py` or `benchmark_cpu.py`.
- [x] 1.2 Verify environment supports `torch.quantization` and `AutoTokenizer` fast mode.

## 2. Core Optimization

- [x] 2.1 Update `DataCleaner.__init__` to use `AutoTokenizer(use_fast=True)` and set `max_length=64`.
- [x] 2.2 Implement dynamic quantization in `DataCleaner.__init__` using `torch.quantization.quantize_dynamic`.
- [x] 2.3 Refactor `predict_ai_batch` to optimize tokenization and handle inference without unnecessary data movement.

## 3. Pipeline Refactoring

- [x] 3.1 Modify `process_async` in `DataCleaner` to remove `MAX_CONCURRENT_CHUNKS` and sequentialize AI inference.
- [x] 3.2 Adjust batch size for sequential inference to balance latency and throughput (target: 64).
- [x] 3.3 Ensure progress callbacks are still triggered correctly in the new sequential flow.

## 4. Validation and Testing

- [x] 4.1 Run accuracy validation tests to ensure quantization doesn't degrade prediction quality.
- [x] 4.2 Measure final throughput and compare against the 20 rows/s target.
- [x] 4.3 Verify the "Clean Data" page functions correctly with the new backend changes.
