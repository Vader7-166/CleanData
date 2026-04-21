## 1. Backend Security Bypass

- [x] 1.1 Modify `backend/main.py`: Comment out `get_current_user` dependency in `@app.post("/upload")`.
- [x] 1.2 Modify `backend/main.py`: Provide a hardcoded `user` (e.g., the admin user) in the upload endpoint to maintain history tracking without real auth.

## 2. Frontend JavaScript Fixes

- [x] 2.1 Modify `frontend/app.js`: Add null checks for `usernameInput` and `passwordInput` at initialization.
- [x] 2.2 Modify `frontend/app.js`: Update the `processBtn` click handler to skip Basic Auth header if credentials are not provided.
- [x] 2.3 Modify `frontend/app.js`: Update the error and reset handlers to gracefully handle missing `authSection` DOM element.

## 3. Frontend Layout & CSS Fixes

- [x] 3.1 Modify `frontend/style.css`: Set `overflow-x: hidden` on `html` and `body` to prevent massive background animation from affecting centering.
- [x] 3.2 Modify `frontend/style.css`: Adjust `.background-animation` to use more stable positioning (e.g., `width: 100vw; height: 100vh; left: 0; top: 0;`).
- [x] 3.3 Modify `frontend/style.css`: Ensure `.glass-container` centering using `flex` is robust and not affected by sibling elements.
- [x] 3.4 Verify the "shifting left" issue is resolved across multiple refreshes.

## 4. Stability Fixes

- [x] 4.1 Fix `bcrypt` compatibility crash in `backend/main.py` startup event by bypassing admin user creation.

