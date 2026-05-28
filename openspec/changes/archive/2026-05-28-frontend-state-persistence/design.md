## Context

The React frontend currently uses volatile memory (useState) for all workflow-specific data. While auth tokens are persisted, the actual progress of data cleaning or dictionary generation is lost upon navigation or refresh.

## Goals / Non-Goals

**Goals:**
- Maintain current wizard step and text inputs in `DictionaryGeneratorWizard` across refreshes.
- Track active `jobId` in `CleanData` so users can see logs even after a reload.
- Provide a clear UI state when a refresh occurs (e.g., "Resuming session...").

**Non-Goals:**
- Persisting binary `File` objects (limited by browser security and localStorage size).
- Implementing a full-blown Redux store.

## Decisions

### 1. `usePersistedState` Custom Hook
- **Decision:** Create a hook that behaves like `useState` but automatically reads from and writes to `localStorage` based on a key.
- **Rationale:** Minimizes boilerplate and makes it easy to add persistence to any existing state variable.

### 2. Auto-resume Logic for SSE
- **Decision:** In `CleanData`, use a `useEffect` that checks for an existing `activeJobId`. If found, it will immediately fetch the current status and, if still processing, re-open the `EventSource` connection.
- **Rationale:** Ensures continuity of the user experience for long-running jobs.

### 3. File Re-selection Handling
- **Decision:** Since we can't save the actual `File` object, we will save the `fileName`. If a refresh happens, the UI will show the name of the file previously used and a message: "Please re-select this file to continue".
- **Rationale:** Transparency. The user knows what was happening and what they need to do to fix the security limitation.

## Risks / Trade-offs

- **[Risk] State Desync** → If the backend finishes a job but the frontend is stale.
- **Mitigation:** Always fetch the latest job status from the API on mount if a `jobId` is present.
- **[Trade-off] LocalStorage Limits** → We won't store large previews, only the metadata needed to fetch them.
