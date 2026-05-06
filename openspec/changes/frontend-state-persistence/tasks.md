## 1. Setup Persistence Layer

- [x] 1.1 Create `frontend/src/hooks/usePersistedState.js` with `localStorage` synchronization.

## 2. Implement Persistence in Clean Data Page

- [x] 2.1 Refactor `CleanData.jsx` to use `usePersistedState` for `activeJobId` and `logs`.
- [x] 2.2 Add `useEffect` logic to automatically resume job tracking if an `activeJobId` is found on mount.
- [x] 2.3 Clear persisted state when a job is completed or reset.

## 3. Implement Persistence in Dictionary Wizard

- [x] 3.1 Refactor `DictionaryGeneratorWizard.jsx` to use `usePersistedState` for `step`, `useLlm`, and `dictName`.
- [x] 3.2 Persist the name of the selected `rawFile` and `reviewedDraftFile`.
- [x] 3.3 Add UI feedback (e.g., "Re-upload required") when files are missing but a previous session is active.

## 4. App-level Consistency

- [x] 4.1 Ensure that navigating between pages doesn't clear the `localStorage` entries (only explicit resets or completions should).
