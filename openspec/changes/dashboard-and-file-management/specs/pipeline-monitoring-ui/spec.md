## MODIFIED Requirements

### Requirement: Real-time Pipeline Progress Logging
The system SHALL emit real-time progress logs detailing each major stage of the data processing pipeline AND persist these logs and overall job statistics (duration, dictionary used, success/error counts) in the database.

#### Scenario: Emit and persist log on stage change
- **WHEN** the backend data pipeline transitions from one processing stage to another
- **THEN** it emits a real-time log event AND updates the persistent job record in the database with current status and metrics.

### Requirement: UI Display of Progress Logs and Job Stats
The frontend SHALL display real-time pipeline progress during processing and provide access to historical job statistics for completed tasks.

#### Scenario: Display historical job stats
- **WHEN** a user views a completed job in the dashboard
- **THEN** the system displays the persisted statistics including processing time, dictionary used, and final row/column counts.
