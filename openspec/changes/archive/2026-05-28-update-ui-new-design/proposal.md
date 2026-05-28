## Why

The current UI uses a custom "glassmorphism" style with Vanilla CSS which is difficult to maintain and extend. The user has provided a new modern design in the `newUI` folder based on Tailwind CSS and a comprehensive UI component library (Shadcn-like). This change aims to migrate the entire frontend to this new design while preserving all existing backend integration and business logic.

## What Changes

- **Style Migration**: Integrate Tailwind CSS and the provided `theme.css` into the Vite project.
- **Layout Overhaul**: Replace the current `MainLayout` and `AuthLayout` with the new `Sidebar` and container structure from `newUI`.
- **Component Replacement**: Replace current page components (`Dashboard`, `CleanData`, `Dictionary`, `DictionaryGenerator`) with the new versions provided, while **merging the existing functional logic** (API calls, SSE streams, state persistence).
- **Navigation Update**: Align routes with the new `App.tsx` structure.
- **TypeScript Support (Optional/Partial)**: Since the new UI is in TypeScript, I will add TypeScript support to the Vite project to ensure these components can be used natively.

## Capabilities

### New Capabilities
- `tailwind-styling`: Integration of Tailwind CSS for modern, maintainable styling.
- `shared-ui-components`: A library of reusable UI components (Button, Card, Input, etc.) from `newUI/app/components/ui`.

### Modified Capabilities
- `sidebar-layout`: Update to the new Sidebar design.
- `clean-data-page`: Apply new UI while keeping SSE and persistence logic.
- `dictionary-management-page`: Apply new UI with existing CRUD operations.
- `dictionary-generation-wizard`: Apply new UI to the multi-step wizard.

## Impact

- `frontend/`: Significant changes to almost all files in `src/`.
- `frontend/package.json`: Addition of Tailwind, Autoprefixer, PostCSS, and potentially TypeScript dependencies.
- `frontend/tailwind.config.js` and `frontend/postcss.config.js`: New configuration files.
- Improved user experience and much easier future UI modifications.
