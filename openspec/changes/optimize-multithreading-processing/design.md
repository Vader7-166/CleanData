## Context

The `DataCleaner` currently runs dictionary matching sequentially across the DataFrame (`df.apply()`) and AI inference sequentially in chunks using a thread pool. While dictionary matching was recently optimized (taking ~8.1 seconds for 1000 rows), processing very large datasets (e.g., 50,000+ rows) still takes substantial time. Furthermore, the AI inference pass can be optimized by maximizing hardware utilization. By introducing multiprocessing for CPU-bound tasks and optimized concurrency for GPU/CPU inference, we can significantly boost throughput.

## Goals / Non-Goals

**Goals:**
- Reduce overall execution time of the `process_async` pipeline.
- Implement parallel dictionary matching to bypass the Global Interpreter Lock (GIL) and utilize multiple CPU cores.
- Implement controlled concurrent AI inference batch processing to maximize throughput without causing Out-Of-Memory (OOM) errors.

**Non-Goals:**
- Modifying or retraining the underlying `AutoModelForSequenceClassification` AI model.
- Restructuring the entire `FastAPI` application architecture.

## Decisions

- **Parallel Dictionary Matching**: We will partition the `pandas` DataFrame into smaller chunks and process them in parallel using Python's `concurrent.futures.ProcessPoolExecutor`. This is favored over `pandarallel` to avoid introducing new heavy dependencies and to maintain fine-grained control over process spawning. Since regex pattern matching is CPU-bound, a process pool will effectively bypass the GIL.
- **Concurrent AI Inference**: AI inference uses PyTorch, which releases the GIL for core operations. However, executing too many concurrent chunks can lead to CPU RAM or GPU VRAM exhaustion. We will refactor the AI loop to use `asyncio.gather` combined with an `asyncio.Semaphore` to limit the maximum number of concurrent chunks (e.g., `MAX_CONCURRENT_CHUNKS = 4`).

## Risks / Trade-offs

- **Risk: GPU/RAM Exhaustion** -> *Mitigation*: The `asyncio.Semaphore` will strictly throttle the number of concurrent model inference calls. The `MAX_CONCURRENT_CHUNKS` limit will be configurable.
- **Risk: Process Spawning Overhead** -> *Mitigation*: We will ensure the DataFrame is partitioned into appropriately sized chunks (e.g., `num_partitions = number of CPU cores`) so that the overhead of spawning processes is negligible compared to the processing time.
