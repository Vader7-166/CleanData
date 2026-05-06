## ADDED Requirements

### Requirement: Automated Cluster Naming
The system SHALL use a Large Language Model to assign context-aware, human-readable names to discovered product clusters.

#### Scenario: LLM naming logic
- **WHEN** clusters are discovered via TF-IDF/DBSCAN
- **THEN** the system SHALL send batch prompts to the Groq API and update cluster names with the response.

### Requirement: Fallback mechanism
The system SHALL fallback to TF-IDF keywords if the LLM API is unavailable or fails.

#### Scenario: API Failure
- **WHEN** the Groq API returns an error or rate limit
- **THEN** the system SHALL use the top TF-IDF tokens as the default cluster name.
