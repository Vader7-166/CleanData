## MODIFIED Requirements

### Requirement: Keyword Frequency Extraction
The system SHALL extract distinguishing keywords for each classification in the taxonomy using a Purity-Weighted Frequency algorithm.

#### Scenario: HS-Code Scoped Purity
- **WHEN** extracting keywords for a taxonomy row
- **THEN** the system SHALL calculate the purity of each candidate keyword relative to all other groups **within the same HS Code**.
- **AND** the system SHALL prioritize keywords that are unique to the group within that HS Code context.
