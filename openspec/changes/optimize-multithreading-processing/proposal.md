## Why

Currently, the `DataCleaner` pipeline processes data sequentially. Although dictionary matching has been optimized, processing 10,000+ rows still relies on a single-threaded approach via Pandas `apply`. Furthermore, AI inference (Pass 2) processes chunks sequentially. By leveraging multithreading or multiprocessing, we can process dictionary mapping and AI inference in parallel, significantly reducing the overall processing time and maximizing CPU/GPU utilization.

## What Changes

- Implement parallel processing for the dictionary matching step (e.g., using `pandarallel` or Python's built-in `multiprocessing` pool).
- Execute AI inference chunks concurrently (using asyncio `gather` with multiple background threads) instead of waiting for each chunk sequentially.
- Optimize the overall asynchronous pipeline in `DataCleaner.process_async` to handle concurrent tasks without exhausting memory.

## Capabilities

### New Capabilities
- `multithreaded-processing`: Introduces concurrent execution for data cleaning passes (dictionary matching and AI batching) to improve throughput and reduce total processing time.

### Modified Capabilities


## Impact

- **Affected Code**: `backend/core/data_cleaner.py` (`process_async`, `predict_dictionary`).
- **Dependencies**: May require adding a library like `pandarallel` to `requirements.txt`.
- **System Impact**: Increased CPU and RAM utilization. Concurrent AI inference might require careful batching to avoid GPU out-of-memory errors if multiple chunks are pushed to the model simultaneously.
