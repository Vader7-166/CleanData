## 1. Diagnostics and Profiling

- [x] 1.1 Add timing markers to `DataCleaner.predict_ai_batch` to measure tokenization and forward pass.
- [x] 1.2 Log average rows/second during a sample run to establish a baseline.

## 2. Optimization

- [x] 2.1 Increase `ai_batch_size` in `process_async` from 64 to 256.
- [x] 2.2 Remove the hardcoded `batch_size=32` inside `predict_ai_batch` and use the passed argument.
- [x] 2.3 Optimize tokenization by setting `padding=True` and `truncation=True` once for the entire batch if not already efficient.
- [x] 2.4 Enable `torch.backends.cudnn.benchmark = True` if using GPU to optimize kernel selection.

## 3. Advanced Parallelization (Optional based on 1.x results)

- [x] 3.1 Implement a pre-tokenization step using a `ThreadPoolExecutor` (achieved via concurrent `asyncio.to_thread` calls).
- [x] 3.2 Adjust `MAX_CONCURRENT_CHUNKS` to balance VRAM usage and throughput (coordinated with batch size increase).

## 4. Validation

- [ ] 4.1 Run a benchmark with 19,000+ rows and compare against the 30-minute baseline.
- [ ] 4.2 Verify that output quality remains consistent (no regression in labels).
