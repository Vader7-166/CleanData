## Context

The backend uses a PhoBERT model for product classification. Current inference on CPU hardware achieves ~3 rows/s, which is a major bottleneck for the data cleaning pipeline. The system lacks quantization and uses an inefficient concurrency model for CPU-bound tasks.

## Goals / Non-Goals

**Goals:**
- Increase AI inference throughput to >20 rows/s on CPU.
- Implement dynamic quantization for the classification model.
- Optimize preprocessing (tokenization) speed and efficiency.
- Refactor the inference pipeline to eliminate CPU contention.

**Non-Goals:**
- GPU optimization (the system is targeted for CPU-only environments).
- Model retraining or architectural changes to the transformer itself.
- Changes to the dictionary matching logic (Pass 1).

## Decisions

### 1. Dynamic Quantization (int8)
- **Rationale**: Dynamic quantization is the most straightforward way to speed up BERT-based models on CPU without requiring specialized hardware or complex calibration. It reduces weight memory bandwidth and utilizes optimized integer kernels.
- **Alternatives**: Static quantization (more complex, requires calibration data) or ONNX Runtime (extra dependency, though potentially faster). Dynamic quantization offers the best effort-to-reward ratio for the current environment.

### 2. AutoTokenizer (Fast) with Reduced Max Length
- **Rationale**: The Rust-backed `AutoTokenizer` is significantly faster at processing batches. Reducing `max_length` from 128 to 64 is safe because the input strings (brand + power + product name) are typically short and don't require long context.
- **Alternatives**: Keeping `PhobertTokenizer` (slower Python implementation) or keeping 128 length (unnecessary padding overhead).

### 3. Sequential Batch Processing
- **Rationale**: PyTorch's internal multithreading (Aten) is highly optimized for utilizing all CPU cores on a single batch. Attempting to run multiple batches concurrently via Python threads leads to context switching overhead and cache trashing. Processing one large batch (or sequential smaller batches) allows the CPU to stay in a high-performance state.
- **Alternatives**: Keeping the `asyncio.to_thread` with `MAX_CONCURRENT_CHUNKS` strategy (proven slow in this specific CPU-bound scenario).

## Risks / Trade-offs

- **[Risk] Accuracy Drop** → Mitigation: Dynamic quantization typically loses <1% accuracy. We will monitor the confidence scores during testing.
- **[Risk] Memory Usage** → Mitigation: Quantization actually reduces the model's memory footprint from ~500MB to ~130MB for weights.
- **[Risk] Torch Version Compatibility** → Mitigation: We verified `torch 2.11.0` is present, which supports the required quantization APIs.
