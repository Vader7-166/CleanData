## ADDED Requirements

### Requirement: State Persistence Across Reloads
The system SHALL persist critical workflow state (job IDs, wizard progress) to the browser's `localStorage` to survive page refreshes and navigation.

#### Scenario: Auto-Resuming a Job
- **GIVEN** a user has started a data cleaning job
- **WHEN** the user refreshes the page or navigates away and back
- **THEN** the system SHALL automatically reconnect to the progress stream (SSE) for that job.

#### Scenario: Persisting Wizard Progress
- **GIVEN** a user is at Step 2 of the Dictionary Generator
- **WHEN** the user reloads the page
- **THEN** the system SHALL remain at Step 2 and keep the previously entered dictionary name.
- **AND** the system SHALL prompt the user to re-select the binary files if they are not cached.
