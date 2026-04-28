## Context

The current frontend is a single monolithic file (`frontend/app.js`) that manages state and UI in a single view. As the project grows, this approach leads to cluttered code and a "crammed" UI.

## Goals / Non-Goals

**Goals:**
- Implement client-side routing using React Router.
- Create a clean Sidebar + Main Content layout.
- Separate features into independent page components.
- Improve visual hierarchy and spacing.

**Non-Goals:**
- Changing the backend API structure (unless routing requires specific entry points).
- Adding complex animation transitions between routes.

## Decisions

### Routing Library
Use a lightweight client-side router (e.g., `React Router` if using React, or a custom `location.pathname` listener for vanilla JS).
**Rationale:** Standard practice for modern web apps to provide bookmarkable URLs and better back-button support.

### Layout Architecture
- **AuthLayout**: Full-screen centered layout for Login/Register.
- **MainLayout**: Persistent sidebar on the left (250px width), top header (optional), and flexible main content area on the right.
**Rationale:** Sidebars provide better accessibility for multiple feature modules compared to top navs or single-page widgets.

### Component Separation
Refactor `app.js` using react to serve as the router/orchestrator. Feature logic for Dashboard, Clean Data, and Dictionary will be moved into separate components.

## Risks / Trade-offs

- **Risk:** Navigation state loss on refresh.
  - **Mitigation:** Use `localStorage` or session-based state management to persist the active route and auth token.
- **Trade-off:** Initial load time might slightly increase as more components are defined, but long-term maintainability is significantly improved.
