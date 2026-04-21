## Why

The requirement is to have a completely anonymous tool without any user management, admin logic, or database tracking of processing history. This simplifies the architecture and eliminates the need for login or password hashing.

## What Changes

- **Backend**:
  - Remove `User` and `ProcessingHistory` models from `backend/models.py`.
  - Remove all authentication dependencies and database session usage in `backend/main.py`.
  - Update the `/upload` endpoint to process files anonymously without recording history to a database.
  - Simplify `startup_event` to only load the model.
- **Frontend**:
  - Remove all UI and logic related to credentials in `frontend/index.html` and `frontend/app.js`.

## Capabilities

### REMOVED Capabilities
- `user-auth`: **Reason**: Tool requested to be fully anonymous. **Migration**: Direct use of /upload endpoint.
- `processing-history`: **Reason**: Requirement to remove all administrative/tracking features.

## Impact

- The database will no longer be used for user or history tracking.
- The system will be faster to initialize and easier to maintain without security dependencies.
