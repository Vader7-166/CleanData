## ADDED Requirements

### Requirement: Frontend interface
The system SHALL provide a web portal allowing the user to select files (Drag-and-Drop or File Picker) and submit them to the backend API.

#### Scenario: File upload works seamlessly
- **WHEN** user drags a CSV file and clicks "Clean"
- **THEN** it displays a loading indicator, then triggers a prompt to download the cleaned Excel/CSV report
