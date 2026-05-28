## Why

Currently, the application state (active processing jobs, wizard progress, form inputs) is stored only in React component memory. This means if a user refreshes the page (F5) or navigates away and back, all progress is lost. This is particularly problematic for long-running AI tasks like dictionary generation or large file cleaning, where a user might accidentally lose their work.

## What Changes

- **Persistence Layer**: Implement a mechanism to sync critical UI state to `localStorage`.
- **Clean Data Page**: Persist the `jobId` and current processing logs so a user can resume monitoring a job after a refresh.
- **Dictionary Generator**: Persist the current wizard step, dictionary name, and metadata about uploaded files (names) so the user doesn't have to re-enter info after a refresh or navigation.
- **Auto-resume Logic**: Add logic to re-connect to SSE streams or fetch results automatically if a pending job is detected on page load.

## Capabilities

### New Capabilities
- `state-persistence`: General mechanism for syncing React state to browser storage.

### Modified Capabilities
- `clean-data-page`: Add auto-resume logic for pending jobs.
- `dictionary-generation-wizard`: Persist wizard progress and inputs.

## Impact

- `frontend/src/hooks/usePersistedState.js`: New custom hook.
- `frontend/src/pages/CleanData.jsx`: Integration with persistence and auto-resume.
- `frontend/src/pages/DictionaryGeneratorWizard.jsx`: Integration with persistence.
- Users will have a much more robust experience, especially when dealing with long-running tasks or accidental page reloads.
