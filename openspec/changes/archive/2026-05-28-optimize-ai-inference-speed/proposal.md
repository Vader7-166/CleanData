## Why

The current AI inference pipeline is significantly slower than desired, processing 19,000 rows in approximately 30 minutes (~10.5 rows/second). This bottleneck delays large-scale data processing and impacts user experience. As Pass 1 (Dictionary Mapping) has already been optimized, Pass 2 (AI Inference) is now the primary area for performance improvement.

## What Changes

- **Inference Batch Size Optimization**: Tune `ai_batch_size` and `MAX_CONCURRENT_CHUNKS` to maximize GPU/CPU utilization.
- **Async Tokenization Pipeline**: Move tokenization out of the main inference loop or parallelize it to prevent CPU-bound tasks from blocking the GPU.
- **Model Inference Performance Profile**: Add performance markers to identify if the bottleneck is in data loading, tokenization, or actual model forward pass.
- **Hardware Acceleration Tuning**: Ensure `torch.autocast` and `dataloader` optimizations are fully utilized.

## Capabilities

### New Capabilities
- `inference-performance-profiling`: Capability to measure and log execution time for tokenization vs. inference.
- `high-throughput-batch-processing`: Optimized batching strategy for BERT-based models.

### Modified Capabilities
- `multithreaded-processing`: Update the concurrency model to better handle AI inference loads.

## Impact

- `backend/core/data_cleaner.py`: Optimization of `predict_ai_batch` and its caller in `process_async`.
- System Resources: Potential increase in VRAM or RAM usage depending on batch size adjustments.
