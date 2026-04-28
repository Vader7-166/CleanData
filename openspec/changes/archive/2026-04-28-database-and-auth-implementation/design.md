## Context

The system needs to transition from a stateless, single-user prototype to a stateful, multi-user application. This requires a structured database and a secure way to manage user sessions.

## Goals / Non-Goals

**Goals:**
- Implement a relational schema for Users, Dictionaries, and Jobs.
- Secure the backend with JWT authentication.
- Restrict frontend access to authenticated users.
- Enable user categorization (Admin vs regular User).

**Non-Goals:**
- Implementing OAuth2/Social logins (staying with simple username/password for now).
- Multi-tenant database isolation (using row-level `user_id` filtering).

## Decisions

### Database Schema (SQLAlchemy/SQLite)
- **User Table**: `id`, `username`, `hashed_password`, `role` (default: 'user').
- **Dictionary Table**: Added `user_id` foreign key.
- **ProcessingJob Table**: Added `user_id` foreign key.
**Rationale:** Standard relational structure to enable filtering and data ownership.

### Authentication Strategy
Use **FastAPI Users** or a custom implementation with **JWT (JSON Web Tokens)**.
**Rationale:** JWT is stateless and works well with modern SPAs (Single Page Applications), making it easy to scale or transition to separate frontend/backend hosting.

### User Categorization
Add a `role` column to the `User` model. Admins will have a specific flag that grants access to a new Admin Dashboard (optional/future) or allows viewing all jobs.

### UI Route Protection
Implement a higher-order component or route guard in `app.js` that checks for a valid token in `localStorage`. If missing, redirect to `/login`.

## Risks / Trade-offs

- **Risk:** Sensitive data exposure if JWT is not handled correctly.
  - **Mitigation:** Use `HTTPOnly` cookies or secure storage, and ensure short expiration times for tokens.
- **Trade-off:** Adding authentication adds complexity to API calls (headers). This is necessary for security.
