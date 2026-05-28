## MODIFIED Requirements

### Requirement: LLM Cluster Labeling Robustness
The system SHALL use robust prompts and JSON parsing when invoking the LLM for cluster labeling to prevent pipeline crashes.

#### Scenario: Handling Nested JSON Responses
- **WHEN** the LLM API returns a nested JSON object for a cluster label (e.g., `{"1": {"Tên": "Đèn LED"}}`)
- **THEN** the system SHALL extract the inner string value and discard the nesting.
- **AND** the system SHALL NOT crash during downstream processes (like `detect_type`) by passing a dictionary object instead of a string.
