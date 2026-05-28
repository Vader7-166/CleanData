## Context

The current data processing pipeline in `backend/core/data_cleaner.py` uses a hybrid approach of dictionary matching (Pass 1) and AI inference (Pass 2). Pass 1 is currently CPU-bound and constrained by the Global Interpreter Lock (GIL) because it uses `ThreadPoolExecutor` with multiple `re.search` calls. Information extraction is also single-threaded. This leads to a performance bottleneck of ~1000 lines/min.

## Goals / Non-Goals

**Goals:**
- Improve data processing throughput by at least 5-10x.
- Reduce time complexity of dictionary matching from O(N*M) to O(N).
- Effectively utilize multi-core CPUs for Pass 1 and information extraction.
- Minimize initialization overhead for worker processes.

**Non-Goals:**
- Modifying the PhoBERT model architecture or training data.
- Changing the frontend UI components (unless necessary for progress reporting).
- Re-implementing the pipeline in another language (e.g., C++ or Rust).

## Decisions

### 1. Aho-Corasick for Keyword Matching
- **Decision**: Replace multiple `re.search` calls with a single-pass Aho-Corasick automaton using the `pyahocorasick` library.
- **Rationale**: Aho-Corasick allows matching an arbitrary number of keywords in a single scan of the text. This is significantly faster than iterating over thousands of regex patterns.
- **Alternative**: `flashtext` was considered but `pyahocorasick` is more mature and widely used in performance-critical Python applications.

### 2. Multiprocessing for CPU-bound Tasks
- **Decision**: Transition Pass 1 and Info Extraction to `concurrent.futures.ProcessPoolExecutor`.
- **Rationale**: Python's GIL prevents true parallel execution of CPU-bound code (like regex or Aho-Corasick) in threads. Multiprocessing bypasses the GIL by using separate memory spaces.
- **Implementation**: Workers will be initialized with the dictionary and Aho-Corasick automaton once using the `initializer` parameter of `ProcessPoolExecutor` to avoid redundant computations.

### 3. Data Chunking and Batching
- **Decision**: Process data in larger chunks (e.g., 5000-10000 rows) when sending to `ProcessPoolExecutor`.
- **Rationale**: Reduces the IPC (Inter-Process Communication) overhead.
- **Decision**: Keep Pass 2 (AI Inference) using `asyncio` and GPU-optimized batching, as it is already relatively efficient and benefits more from I/O concurrency and GPU parallelism.

### 4. Separate Dictionary from Model
- **Decision**: Create a `DictionaryMatcher` class that does not depend on the large Transformers model.
- **Rationale**: This allows spawning worker processes quickly without loading the multi-gigabyte PhoBERT model into every process's memory.

## Risks / Trade-offs

- **[Risk] Memory Usage** → Spawning many processes, each with a copy of the dictionary, might consume significant RAM.
  - **Mitigation**: Use a shared-memory approach if necessary (e.g., `multiprocessing.shared_memory`) or limit the number of workers based on available RAM.
- **[Risk] IPC Overhead** → Sending large DataFrames between processes can be slow.
  - **Mitigation**: Send only the necessary columns (`input_for_ai`) and use efficient serialization (Pickle/Parquet).
- **[Risk] Complexity** → Managing process life-cycles and initializers adds complexity.
  - **Mitigation**: Wrap the logic in a clean `DictionaryMatcher` and `ProcessPoolManager`.
