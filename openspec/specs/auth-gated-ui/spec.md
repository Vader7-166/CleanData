## MODIFIED Requirements

### Requirement: Authentication Guard for Protected Routes
The frontend SHALL protect all functional routes (e.g., `/dashboard`, `/clean-data`, `/dictionary`) by verifying a valid session token before rendering the component.

#### Scenario: Redirect Unauthenticated User from Dashboard
- **WHEN** an unauthenticated guest attempts to access the `/dashboard` URL
- **THEN** the system SHALL redirect them to the `/login` page.

## ADDED Requirements

### Requirement: Authentication Guard for Protected Routes
The frontend SHALL protect routes like `/dashboard` and `/dictionaries` by verifying the presence of a valid session token.

#### Scenario: Redirect Unauthenticated User
- **WHEN** an unauthenticated guest attempts to access the `/dashboard` URL
- **THEN** the system SHALL redirect them to the `/login` page.

### Requirement: Persistent Auth State
The frontend SHALL persist the authentication state across page reloads.

#### Scenario: Auto-login on Reload
- **WHEN** a logged-in user reloads the page and has a valid token in storage
- **THEN** the system SHALL maintain their session and allow continued access to protected features.
