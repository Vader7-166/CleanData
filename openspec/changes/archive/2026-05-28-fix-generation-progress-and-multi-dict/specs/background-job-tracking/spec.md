## ADDED Requirements

### Requirement: Background Job Tracking
The system SHALL track long-running jobs (like LLM labeling) asynchronously on the backend and persist their state, allowing the client to query or resume watching the progress even after navigating away and returning.

#### Scenario: Client Re-connects to Active Job
- **WHEN** a user starts a Dictionary Generation job and navigates to another page, then returns
- **THEN** the system SHALL recognize the active job and resume displaying its current status without starting a new job.
