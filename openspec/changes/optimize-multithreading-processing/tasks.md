## 1. Preparation

- [x] 1.1 Add `MAX_CONCURRENT_CHUNKS` setting (e.g., set to 4) to `DataCleaner` initialization to control AI concurrency.
- [x] 1.2 Determine if a `ProcessPoolExecutor` or `ThreadPoolExecutor` will be used for dictionary matching and ensure thread safety of the dictionary inverted index. (Decision: ThreadPoolExecutor to avoid pickling PyTorch model).

## 2. Parallel Dictionary Matching

- [x] 2.1 Refactor `DataCleaner.process_async` to partition the DataFrame into equal-sized chunks based on the number of available CPU cores.
- [x] 2.2 Implement a pool executor (using `loop.run_in_executor`) to execute `predict_dictionary` over the partitions concurrently.
- [x] 2.3 Re-assemble the results from the partitions and align them correctly with the main DataFrame `df_clean`.

## 3. Concurrent AI Inference

- [x] 3.1 Refactor the AI fallback logic in `DataCleaner.process_async` to execute the `process_chunk` tasks concurrently using `asyncio.gather`.
- [x] 3.2 Implement an `asyncio.Semaphore` using `MAX_CONCURRENT_CHUNKS` to wrap the AI chunk execution, preventing VRAM/RAM exhaustion.
- [x] 3.3 Ensure that the resulting lists of AI predictions are properly merged and assigned back to the `df_clean` DataFrame.

## 4. Verification & Benchmarking

- [x] 4.1 Create a test script to benchmark the performance difference between sequential and concurrent execution over 1000+ rows.
- [x] 4.2 Verify that the outputs (including `Mã HS` and segment splits) are identical to the expected sequential output.
