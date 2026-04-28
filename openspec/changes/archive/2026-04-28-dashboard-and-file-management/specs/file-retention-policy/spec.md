## ADDED Requirements

### Requirement: Maximum File Retention Limit
The system SHALL limit the number of stored files to the 10 most recent uploads.

#### Scenario: Automatically Delete Oldest File
- **WHEN** a user uploads a new file and the total count of stored files exceeds 10
- **THEN** the system SHALL automatically delete the oldest file (based on upload timestamp) from both storage and the database to maintain the 10-file limit.
