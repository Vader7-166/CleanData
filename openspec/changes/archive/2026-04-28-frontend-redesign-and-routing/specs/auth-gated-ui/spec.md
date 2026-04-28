## MODIFIED Requirements

### Requirement: Authentication Guard for Protected Routes
The frontend SHALL protect all functional routes (e.g., `/dashboard`, `/clean-data`, `/dictionary`) by verifying a valid session token before rendering the component.

#### Scenario: Redirect Unauthenticated User from Dashboard
- **WHEN** an unauthenticated guest attempts to access the `/dashboard` URL
- **THEN** the system SHALL redirect them to the `/login` page.
