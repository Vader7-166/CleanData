## 1. Model Cleanup

- [x] 1.1 Remove `User` and `ProcessingHistory` models from `backend/models.py`.

## 2. Backend Cleanup

- [x] 2.1 Remove `passlib`, `security`, and `Session` dependencies from `backend/main.py`.
- [x] 2.2 Simplify `startup_event` in `backend/main.py`: Remove DB initialization and admin creation.
- [x] 2.3 Refactor `/upload` in `backend/main.py`: Remove `user` and `db` dependencies and history recording.

## 3. Frontend Cleanup

- [x] 3.1 Remove commented-out `authSection` from `frontend/index.html`.
- [x] 3.2 Remove all `usernameInput`, `passwordInput`, and credential logic from `frontend/app.js`.
- [x] 3.3 Ensure `fetch` call in `frontend/app.js` doesn't send auth headers.

## 4. Requirement Optimization

- [x] 4.1 Remove `passlib[bcrypt]` and `bcrypt` from `backend/requirements.txt` since they are no longer needed.
