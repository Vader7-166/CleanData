## ADDED Requirements

### Requirement: Dictionary File Upload
The system SHALL provide an endpoint to upload CSV files to be used as dictionaries for product classification.

#### Scenario: Successful CSV Upload
- **WHEN** a user uploads a valid CSV file through the dictionary upload endpoint
- **THEN** the system SHALL store the file in the designated dictionary storage directory and record its metadata (name, upload time) in the database.

#### Scenario: Invalid File Type Upload
- **WHEN** a user attempts to upload a non-CSV file
- **THEN** the system SHALL reject the upload and return an error message indicating that only CSV files are supported.

### Requirement: Dictionary File Persistence
The system SHALL persist uploaded dictionary files across application restarts.

#### Scenario: Dictionary Recovery After Restart
- **WHEN** the application is restarted
- **THEN** the system SHALL successfully retrieve and list all previously uploaded dictionary files.
