## ADDED Requirements

### Requirement: Performance Profiling
The system SHALL measure and log the execution time of major inference stages (Tokenization, Forward Pass, Post-processing) when a debug flag is enabled.

#### Scenario: Measuring inference performance
- **WHEN** AI inference is running on a batch of data
- **THEN** the system logs the duration of the tokenization phase
- **THEN** the system logs the duration of the model forward pass
- **THEN** the system logs the overall throughput (rows/second).

### Requirement: Optimized Batch Processing
The system SHALL use configurable and optimized batch sizes to maximize hardware utilization.

#### Scenario: Processing with larger batches
- **WHEN** a large number of rows fallback to AI inference
- **THEN** the system groups them into batches of at least 128 (configurable)
- **THEN** the system processes these batches on the GPU with `torch.autocast` enabled for mixed-precision acceleration.
