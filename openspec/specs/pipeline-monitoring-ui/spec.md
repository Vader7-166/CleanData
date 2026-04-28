## ADDED Requirements

### Requirement: Real-time Pipeline Progress Logging
The system SHALL emit real-time progress logs (e.g., via SSE or WebSockets) detailing each major stage of the data processing pipeline (e.g., "Filtering", "Cleaning", "Predicting", "Done").

#### Scenario: Emit log on stage change
- **WHEN** the backend data pipeline transitions from one processing stage to another
- **THEN** it emits a log event containing the stage name and status.

### Requirement: UI Display of Progress Logs
The frontend SHALL connect to the real-time logging endpoint and display the pipeline progress to the user.

#### Scenario: Display new log event
- **WHEN** the frontend receives a log event from the backend
- **THEN** it appends the log message to the UI log console or progress indicator.
