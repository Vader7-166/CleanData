## ADDED Requirements

### Requirement: Real-time Progress Indicator
The UI SHALL display real-time progress updates for long-running processes (e.g. LLM labeling and clustering) indicating the number of processed clusters or batches.

#### Scenario: User Monitors Generation Progress
- **WHEN** the dictionary generation step 1 is running
- **THEN** the UI SHALL show a visual progress indicator detailing the current processing stage (e.g., "Batch 1 of 5").
