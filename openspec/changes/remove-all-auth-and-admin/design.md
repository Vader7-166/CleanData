## Context

The user has specifically requested to remove the admin and user moderation features entirely. This means the tool should transition from a multi-user, history-tracking app to a stateless data-processing utility.

## Goals / Non-Goals

**Goals:**
- Completely remove `User` and `ProcessingHistory` models.
- Simplify the backend to eliminate database session dependencies where they aren't needed.
- Clean up the frontend of any leftover auth-related code.

## Decisions

- **Database Usage**: Keep `database.py` for now (to avoid breaking things) but stop using it for history. If possible, remove database usage entirely if the user doesn't need any persistent state.
- **Stateless Processing**: The `/upload` endpoint will now only care about the file and return the result.
- **Frontend Refactor**: The `app.js` will no longer include the `Authorization` header in the `fetch` request.

## Risks / Trade-offs

- **[Risk]** Removing history means no way to track who processed what.
  - **Mitigation**: This is explicitly what the user requested.
