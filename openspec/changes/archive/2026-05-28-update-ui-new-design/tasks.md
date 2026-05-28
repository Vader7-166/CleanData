## 1. Project Infrastructure & Dependencies

- [x] 1.1 Install Tailwind CSS dependencies (`tailwindcss`, `postcss`, `autoprefixer`).
- [x] 1.2 Install UI utility dependencies (`clsx`, `tailwind-merge`).
- [x] 1.3 Add TypeScript support (`typescript`, `@types/react`, `@types/react-dom`, `@types/node`).
- [x] 1.4 Initialize Tailwind and PostCSS configurations.
- [x] 1.5 Update `vite.config.js` to handle TypeScript and Tailwind.

## 2. Shared Assets & Components

- [x] 2.1 Copy components from `newUI/app/components/ui` to `frontend/src/components/ui`.
- [x] 2.2 Copy styles from `newUI/styles` to `frontend/src/styles`.
- [x] 2.3 Integrate `index.css` and `theme.css` into the main entry point (`main.jsx`).

## 3. Layout & Navigation

- [x] 3.1 Create new `Sidebar` component based on `newUI/app/components/Sidebar.tsx`.
- [x] 3.2 Implement the new `MainLayout` using the Sidebar and a scrollable content area.
- [x] 3.3 Update `App.jsx` (or convert to `App.tsx`) to use the new layout and route structure.

## 4. Page Migration (Functional Logic)

- [x] 4.1 Migrate `Dashboard.jsx` to the new design, replacing mock data with actual API calls.
- [x] 4.2 Migrate `CleanData.jsx` to the new design, preserving SSE and persistence logic.
...
- [x] 4.3 Migrate `Dictionary.jsx` to the new design with existing CRUD operations.
- [x] 4.4 Migrate `DictionaryGenerator.jsx` and `DictionaryGeneratorWizard.jsx` to the new design, replacing the "Coming Soon" placeholder with the actual 2-step wizard logic.

## 5. Polish & Verification

- [x] 5.1 Ensure responsive design works as expected across all migrated pages.
- [x] 5.2 Verify that the `usePersistedState` hook and SSE streams are fully functional in the new UI.
- [x] 5.3 Test the authentication flow (Login/Register) with the new layout if applicable.
