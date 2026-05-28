## Why

The current AI inference performance is approximately 3 rows/second on CPU-only hardware. This bottleneck causes significant delays when processing large datasets (thousands of rows). The slow speed is primarily due to the lack of CPU-specific optimizations (quantization), suboptimal tokenizer choice, and CPU oversubscription caused by concurrent inference batches fighting for resources.

## What Changes

- **Model Optimization**: Apply dynamic `int8` quantization to the PhoBERT model to reduce latency on CPU.
- **Tokenizer Update**: Switch to the fast, Rust-backed `AutoTokenizer` and reduce sequence `max_length` from 128 to 64 to minimize preprocessing time.
- **Inference Pipeline Refactoring**: Change the concurrent AI batch processing in `process_async` to a sequential batching strategy to allow PyTorch to utilize internal CPU multithreading more efficiently.

## Capabilities

### New Capabilities
- `high-throughput-inference`: Define performance benchmarks and optimization requirements for CPU-based model inference.

### Modified Capabilities
- `clean-data-page`: Update the data processing requirements to incorporate the new optimized inference pipeline.

## Impact

- **Backend**: `backend/core/data_cleaner.py` will be significantly refactored.
- **Performance**: Expected increase in inference speed from 3 rows/s to >20 rows/s on comparable CPU hardware.
- **Resources**: Reduced CPU contention during the "AI Inference" stage of processing.
