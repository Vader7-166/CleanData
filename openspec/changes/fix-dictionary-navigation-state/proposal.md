## Why

Users are experiencing several workflow blockers that disrupt data cleaning and dictionary generation operations. First, there is no way to delete existing dictionaries, causing clutter and potential use of outdated mappings. Second, navigating between different application pages (like switching from Clean Data to Dictionary management) causes the frontend state to reset, losing selected files and requiring users to re-upload them. Finally, the dictionary generation wizard only allows selecting a single raw file at a time, preventing batch dictionary generation from multiple raw sources.

## What Changes

- Add a delete endpoint to the backend to physically remove dictionary files.
- Add a "Delete" button with a confirmation dialog to the Dictionary Management UI.
- Implement global state management or lift state up (e.g., using React Context or higher-level component state) for file uploads so that file objects and paths persist across route changes.
- Update the `<input type="file">` element in the Dictionary Generation wizard to include the `multiple` attribute, allowing users to select and process multiple raw files simultaneously.

## Capabilities

### New Capabilities
- `frontend-state-persistence`: Ensure that file selections and upload states are preserved when navigating between different application views to prevent data loss and repetitive tasks.

### Modified Capabilities
- `dictionary-management-page`: Add functionality to permanently delete dictionaries from storage.
- `dictionary-upload-storage`: Enable multiple file selection when uploading raw datasets for dictionary generation.

## Impact

- `frontend/src/pages/*`: Components will need to be refactored to consume persistent state or routing mechanisms that preserve state.
- `frontend/src/components/DictionaryGenerator`: The file input needs to support `multiple` and handle an array of files.
- `backend/main.py` (or API routers): Needs a new DELETE endpoint for dictionaries.
