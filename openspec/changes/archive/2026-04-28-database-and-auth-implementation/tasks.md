## 1. Database Schema Implementation

- [x] 1.1 Create `User` model in `backend/models.py`.
- [x] 1.2 Update `Dictionary` and `ProcessingJob` models with `user_id` foreign key.
- [x] 1.3 Update database initialization logic to create new tables.

## 2. Backend Authentication Setup

- [x] 2.1 Install dependencies for password hashing (`passlib`) and JWT (`python-jose`).
- [x] 2.2 Implement password hashing and verification utilities.
- [x] 2.3 Create `/api/auth/register` and `/api/auth/login` endpoints.
- [x] 2.4 Implement `get_current_user` dependency for securing API routes.

## 3. Frontend Authentication & Gating

- [x] 3.1 Create Login and Register components in the frontend.
- [x] 3.2 Implement authentication service to manage tokens and API headers.
- [x] 3.3 Add route guards to `app.js` to protect dashboard and dictionary views.
- [x] 3.4 Implement "Logout" functionality and token expiration handling.

## 4. Feature Integration & Scoping

- [x] 4.1 Update Dictionary upload to use the current user's ID.
- [x] 4.2 Update Dashboard list API to filter results by `user_id`.
- [x] 4.3 Update Retention Policy logic to count files per user.
- [x] 4.4 Add role-based checks for administrative features.
