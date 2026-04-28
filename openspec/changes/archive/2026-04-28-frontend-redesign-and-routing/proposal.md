## Why

The current single-widget UI is becoming overcrowded and difficult to maintain as new features like dictionary management and dashboard history are added. Transitioning to a multi-page architecture with dedicated routes will improve user experience, provide better organization of features, and allow for a cleaner, more professional layout.

## What Changes

- **BREAKING**: Replace the single-page "all-in-one" widget with a multi-page routing system using React Router.
- Implement a global Layout with a persistent Sidebar Navigation.
- Create dedicated pages for:
    - Auth (Login/Register).
    - Dashboard (Overview and history).
    - Clean Data (Upload, processing, and preview).
    - Dictionary (Storage, stats, and management).
- Integrate a routing library (e.g., React Router or native JS routing logic).

## Capabilities

### New Capabilities
- `multi-page-routing`: System for navigating between different views/pages.
- `sidebar-layout`: A consistent UI shell with a side navigation bar and main content area.
- `clean-data-page`: Dedicated view for file uploads, processing logic, and result preview.
- `dictionary-management-page`: Dedicated view for dictionary storage, usage statistics, and management.

### Modified Capabilities
- `auth-gated-ui`: Requirements updated to handle route-level protection for the new multi-page structure.
- `file-history-dashboard`: Requirements updated to reside on its own dedicated dashboard page.

## Impact

- Frontend: Complete restructuring of `app.js` (or splitting into multiple components/files).
- Styles: Major CSS updates for layout, sidebar, and page-specific containers.
- Routing: Introduction of client-side routing.
