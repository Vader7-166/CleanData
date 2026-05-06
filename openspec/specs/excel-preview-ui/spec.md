## ADDED Requirements

### Requirement: Final Output Excel Preview API
The backend SHALL provide an endpoint or data payload containing a preview (e.g., first 100 rows) of the final processed Excel data in a web-friendly format (JSON or HTML).

#### Scenario: Request preview data
- **WHEN** data processing completes
- **THEN** the backend makes the preview data available for the frontend to consume.

### Requirement: Render Excel Preview in UI
The frontend SHALL render a tabular preview of the final processed Excel data before the user downloads the complete file.

#### Scenario: Display data preview
- **WHEN** the data processing completes and preview data is received
- **THEN** the UI displays an interactive or static table showing the preview data to the user.
