## MODIFIED Requirements

### Requirement: Maximum File Retention Limit
The system SHALL limit the number of stored files to the 10 most recent uploads per user.

#### Scenario: Automatically Delete Oldest File for User
- **WHEN** a user uploads a new file and their personal total count of stored files exceeds 10
- **THEN** the system SHALL automatically delete the oldest file belonging to THAT user.
