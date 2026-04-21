## Context

The project is a "Data Cleaner Pro" application with a FastAPI backend and a Vanilla JS/CSS frontend. The user wants to temporarily bypass security for development and fix a strange layout bug where the main container shifts left on every refresh.

## Goals / Non-Goals

**Goals:**
- Enable file upload without authentication on the backend.
- Prevent JavaScript crashes on the frontend when authentication inputs are missing.
- Fix the `glass-container` shifting issue on the frontend.
- Maintain the aesthetic of the "glassmorphism" design.

**Non-Goals:**
- Permanent removal of security features (this is a temporary bypass).
- Rewriting the frontend in a framework like React.

## Decisions

- **Backend Security Bypass**: 
  - Instead of removing `get_current_user`, we will modify the `upload_file` endpoint to treat the `user` dependency as optional or provide a "mock" admin user if authentication fails or is bypassed.
  - Decision: Modify `upload_file` to use a default admin user if no credentials are provided, or simply comment out the `user: User = Depends(get_current_user)` requirement and use a hardcoded user ID for history tracking.
  - Rationale: Minimizes changes to the codebase while achieving the goal of bypassing the login wall.

- **Frontend JS Fix**:
  - Add null checks for `usernameInput` and `passwordInput` in `app.js`.
  - Update the `processBtn` click handler to skip auth if the inputs are missing or hidden.

- **Frontend Layout Fix**:
  - The "shifting left" issue is likely due to the `background-animation` having `width: 200%` and `left: -50%` combined with `overflow: hidden` on the body. Some browsers struggle with flex centering when there are massive overflowing elements, even if they are absolutely positioned.
  - Decision: Change `background-animation` to use `width: 100vw` and `height: 100vh` with `fixed` positioning, or ensure `overflow-x: hidden` is explicitly set on `html` and `body`.
  - Also, we will disable the `transition` on load to prevent any "snap" effects.

## Risks / Trade-offs

- **[Risk]** Security bypass might be accidentally committed to production.
  - **Mitigation**: Use clear `TODO: SECURITY BYPASS` comments.
- **[Risk]** The layout fix might not be reproducible in all browsers.
  - **Mitigation**: Use standard flexbox centering and avoid negative absolute positioning that exceeds viewport boundaries if possible.
