## ADDED Requirements

### Requirement: Anonymous File Upload
The system SHALL allow users to upload files for processing without providing authentication credentials.

#### Scenario: Upload without credentials
- **WHEN** a user selects a valid file and clicks "Clean Data"
- **THEN** the system SHALL process the file and return a download link without asking for login
