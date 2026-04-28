## Why

The application currently lacks a persistent database and user authentication system, which is essential for managing user-specific data, enforcing storage limits, and securing access to the dashboard and management tools. This change establishes the foundation for a multi-user environment where data and dictionaries are scoped to individual users.

## What Changes

- Implement a robust database schema using SQLAlchemy to support users, dictionaries, and processing jobs.
- Add a user authentication system (Login/Register) using JWT or sessions.
- **BREAKING**: Modify existing UI to require authentication before accessing the dashboard and dictionary management features.
- Associate dictionaries and processing jobs with specific user accounts.
- Enforce user-based file retention policies (10 files per user).

## Capabilities

### New Capabilities
- `user-authentication`: Secure login and registration system to identify and categorize users.
- `database-schema-core`: Implementation of the central database models (Users, Dictionaries, Jobs) and their relationships.
- `auth-gated-ui`: A frontend protection mechanism that redirects unauthenticated users to a login page.

### Modified Capabilities
- `dictionary-upload-storage`: Update to associate uploaded dictionaries with the authenticated user.
- `file-history-dashboard`: Update to display only the files and jobs belonging to the logged-in user.
- `file-retention-policy`: Enforce the 10-file limit on a per-user basis.

## Impact

- Backend: Significant updates to `main.py` for auth middleware, `models.py` for comprehensive schema, and API endpoints to handle user context.
- Frontend: New login/register pages, protected route logic, and updated API calls to include authentication tokens.
- Security: Introduction of password hashing and secure token management.
