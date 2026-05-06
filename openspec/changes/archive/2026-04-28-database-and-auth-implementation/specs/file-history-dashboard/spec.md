## MODIFIED Requirements

### Requirement: Central File Management Dashboard
The system SHALL provide a dashboard view that lists ONLY the files uploaded and processed by the currently authenticated user.

#### Scenario: View User-Specific File List
- **WHEN** an authenticated user navigates to the dashboard
- **THEN** the system SHALL fetch and display ONLY the files associated with their `user_id`.
