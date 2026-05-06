## ADDED Requirements

### Requirement: User Registration
The system SHALL allow new users to create an account with a unique username and a secure password.

#### Scenario: Successful Registration
- **WHEN** a guest provides a unique username and a valid password
- **THEN** the system SHALL hash the password and store the new user record in the database.

### Requirement: Secure User Login
The system SHALL provide a login mechanism that authenticates users and issues a secure session token (JWT).

#### Scenario: Successful Login
- **WHEN** a user provides correct credentials
- **THEN** the system SHALL return a session token and allow access to protected features.

### Requirement: User Categorization
The system SHALL support different user roles (e.g., User, Admin) to manage access levels.

#### Scenario: Admin Access
- **WHEN** a user with the 'Admin' role logged in
- **THEN** the system SHALL grant access to administrative tools and cross-user statistics.
