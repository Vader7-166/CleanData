## ADDED Requirements

### Requirement: Inference Consistency Check
The system SHALL provide a diagnostic utility to verify that unique inputs to the AI model result in varied output logits and labels.

#### Scenario: Running diagnostics on distinct inputs
- **WHEN** the diagnostic script is executed with a set of diverse product descriptions
- **THEN** the system logs the predictions for each sample
- **THEN** it confirms that the results are not identical across the entire set.

### Requirement: Input Traceability
The system SHALL log the exact strings being sent to the PhoBERT tokenizer when debug logging is enabled.

#### Scenario: Verifying pre-inference input
- **WHEN** a batch of data is sent to the AI fallback pass
- **THEN** the system logs a sample of the constructed `input_for_ai` strings
- **THEN** a developer can verify that the strings contain actual product data and are not empty or repetitive.
