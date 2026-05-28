## Why

The current data processing pipeline is limited to approximately 1000 lines per minute, which is insufficient for large-scale datasets. Key bottlenecks identified include Python's Global Interpreter Lock (GIL) affecting CPU-bound regex operations in Pass 1 (Dictionary Matching), single-threaded information extraction, and O(N*M) complexity in the current dictionary search algorithm.

## What Changes

- **Dictionary Matching Optimization**: Replace the iterative regex-based search with the Aho-Corasick algorithm for O(N) complexity matching.
- **Multiprocessing Support**: Transition CPU-bound tasks (Dictionary Matching and Info Extraction) from `ThreadPoolExecutor` to `ProcessPoolExecutor` to bypass GIL limitations.
- **Batch Processing Enhancements**: Optimize AI inference batching and tune concurrency parameters for Pass 2.
- **Dependency Update**: Add `pyahocorasick` to `backend/requirements.txt`.
- **Logic Refinement**: Update `DataCleaner` to separate model loading from dictionary initialization to reduce process spawning overhead.

## Capabilities

### New Capabilities
- `high-performance-matching`: Implements Aho-Corasick based keyword matching with "consumption" logic for high-speed dictionary lookup.
- `multiprocess-pipeline-orchestration`: Provides a robust orchestration layer for distributing data chunks across multiple CPU cores.

### Modified Capabilities
- `dictionary-filtering`: Update the matching requirements to support faster lookup while maintaining scoring integrity and tie-breaker rules.
- `multithreaded-processing`: Transition existing threading logic to a hybrid model that uses multiprocessing for CPU-bound tasks and threading/async for I/O and AI inference.

## Impact

- `backend/core/data_cleaner.py`: Major refactoring of processing logic.
- `backend/requirements.txt`: New dependency on `pyahocorasick`.
- `backend/main.py`: Potential changes in how the cleaner is initialized and managed.
- System Resources: Increased CPU utilization during processing due to multiple worker processes.
