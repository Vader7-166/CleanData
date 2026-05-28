## ADDED Requirements

### Requirement: Dictionary Usage Tracking
The system SHALL record which dictionary was used for each file processed by the pipeline.

#### Scenario: Log Dictionary Usage
- **WHEN** a file is successfully processed using a specific dictionary
- **THEN** the system SHALL store a record linking the processed file to the dictionary used.

### Requirement: Display Usage Statistics
The system SHALL display statistics showing how many files have been processed using each dictionary.

#### Scenario: View Usage Stats
- **WHEN** a user views the dictionary usage statistics dashboard
- **THEN** the system SHALL show a summary report listing each dictionary and the total count of files it has successfully classified.
