## ADDED Requirements

### Requirement: Unified Data Model
The system SHALL implement a relational database schema that links users to their dictionaries and processing history.

#### Scenario: User-Dictionary Relationship
- **WHEN** a user uploads a dictionary
- **THEN** the database record for that dictionary SHALL contain a foreign key referencing the `User` who uploaded it.

#### Scenario: User-Job Relationship
- **WHEN** a processing job is started
- **THEN** the `ProcessingJob` record SHALL be linked to the `User` who initiated the task.

### Requirement: Data Integrity
The database SHALL enforce referential integrity across all models (Users, Dictionaries, Jobs).

#### Scenario: Cascading Deletion
- **WHEN** a user account is deleted
- **THEN** the system SHALL also remove or anonymize all associated dictionaries and job history records.
