## Context

Pass 2 of the data pipeline uses a PhoBERT model for classification. The current implementation processes rows that failed Pass 1 in chunks of 64, with a concurrency limit of 4 chunks at a time. Within each chunk, inference is done in sub-batches of 32. This results in small, inefficient batches for the GPU and serial tokenization which blocks the inference pipeline.

## Goals / Non-Goals

**Goals:**
- Achieve at least 50-100 rows/second throughput for AI inference (up from ~10).
- Fully utilize GPU resources by using larger batch sizes.
- Overlap CPU-bound tokenization with GPU-bound inference.

**Non-Goals:**
- Changing the model weights or architecture.
- Replacing PyTorch with another runtime (e.g., ONNX) unless simpler optimizations fail.

## Decisions

### 1. Increase Batch Size and Concurrency
- **Decision**: Increase `ai_batch_size` to 128 or 256 and adjust `MAX_CONCURRENT_CHUNKS` based on available hardware.
- **Rationale**: Deep learning models are significantly more efficient with larger batches due to vectorized operations and reduced kernel launch overhead.

### 2. Prefetching and Parallel Tokenization
- **Decision**: Use `multiprocessing` to tokenize data in parallel before it reaches the inference loop.
- **Rationale**: Tokenization is a heavy CPU task. By the time the GPU is ready for the next batch, the tokenized tensors should already be in memory.

### 3. Profiling and Performance Monitoring
- **Decision**: Wrap the inference loop with timing markers to log average time spent in "Tokenization" vs "Model Forward" vs "Post-processing".
- **Rationale**: Data-driven optimization is required to ensure we are attacking the correct bottleneck.

## Risks / Trade-offs

- **[Risk] Out of Memory (OOM)** → Large batches consume significant VRAM.
  - **Mitigation**: Implement a dynamic batch size or start with a safe default (128) and provide a configuration parameter.
- **[Risk] IPC Overhead** → Sending large tokenized tensors between processes can be slower than tokenizing in-place.
  - **Mitigation**: Only parallelize if profiling shows tokenization taking >30% of total time.
