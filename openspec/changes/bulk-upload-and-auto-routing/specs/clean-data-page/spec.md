## MODIFIED Requirements

### Requirement: Bulk File Upload and Management
The Clean Data page SHALL support uploading and configuring multiple files at once.

#### Scenario: Multi-file Selection
- **WHEN** the user clicks the upload button on the Clean Data page
- **THEN** the system SHALL allow selecting multiple files from the local file system.

#### Scenario: Review Auto-Mappings
- **WHEN** multiple files are uploaded
- **THEN** the system SHALL display a list of all uploaded files.
- **AND** for each file, it SHALL display the automatically suggested dictionary (if any).
- **AND** it SHALL allow the user to change the dictionary selection for any file.

#### Scenario: Batch Processing Start
- **WHEN** the user clicks "Process All"
- **THEN** the system SHALL initiate a separate background task for each file-dictionary pair.
