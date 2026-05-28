## Context

The user has provided a modern UI design in the `newUI` folder. This design uses Tailwind CSS, TypeScript, and a Shadcn-like component architecture. The current frontend is written in JavaScript with custom CSS. This design document outlines the technical strategy for migrating the existing functionality into the new aesthetic.

## Goals / Non-Goals

**Goals:**
- Migrate the frontend to the new UI design using Tailwind CSS.
- Add TypeScript support to the project to leverage the provided `.tsx` components.
- Merge existing business logic (API integration, SSE, state persistence) into the new UI shells.
- Replace the "Coming Soon" sections in the provided components with actual functional logic from the current app.

**Non-Goals:**
- Changing the backend API.
- Replacing the `react-router-dom` navigation entirely if not necessary (though the new UI uses `react-router`, we will aim for compatibility).
- Rewriting the core data processing logic.

## Decisions

### 1. Hybrid TypeScript/JavaScript Environment
- **Decision**: Update `vite.config.js` and add `tsconfig.json` to support TypeScript.
- **Rationale**: The provided UI is highly typed and uses Shadcn components that rely on TypeScript interfaces. Migrating to TS ensures we don't break these components while allowing existing JS files to be converted incrementally.

### 2. Integration of Shadcn-style Components
- **Decision**: Copy all components from `newUI/app/components/ui` to `src/components/ui`.
- **Rationale**: These are the building blocks of the new UI. We will use them to reconstruct the functional parts of the app (like the Dictionary Generator wizard).

### 3. Merging Logic into Mockups
- **Decision**: For pages like `DictionaryGenerator` and `CleanData`, we will use the structure from `newUI` but re-implement the state management and API calls from the current `.jsx` versions.
- **Rationale**: The provided `DictionaryGenerator.tsx` is only a placeholder. We need to preserve the complex 2-step process and persistence logic recently implemented.

### 4. Style Consolidation
- **Decision**: Use `tailwind.css` and `theme.css` from `newUI` as the primary style source.
- **Rationale**: This defines the new look and feel (Sidebar, Colors, Typography).

## Risks / Trade-offs

- **[Risk] Library Conflict**: `react-router` (v7) vs `react-router-dom` (v6).
- **Mitigation**: Standardize on the version that works best with the current layout while supporting the `Link` and `useLocation` hooks used in the new UI.
- **[Risk] Missing Functionality in UI**: The new UI might lack specific features (like the LLM toggle checkbox).
- **Mitigation**: Add these features using the new style guide (Tailwind classes).
- **[Trade-off] Effort**: Migrating to TS and Tailwind is a significant change compared to just updating CSS.
- **Rationale**: The long-term maintenance and aesthetic quality of the provided design justify the effort.
