## Why

Manually uploading and configuring each data file with its corresponding dictionary is inefficient for users with large batches of data. By allowing bulk uploads and automatically routing files to the correct dictionaries based on standardized naming conventions, we can significantly streamline the data processing workflow.

## What Changes

- **Bulk File Upload**: Enable users to select and upload multiple files simultaneously in the frontend.
- **Auto-Routing Engine**: Implement backend logic to automatically match uploaded raw files to existing dictionaries using naming patterns (e.g., a file named `7020-NK-Th12.2025` will be automatically paired with `dict_7020_2025`).
- **Naming Convention Hints**: Provide users with clear suggestions and documentation on how to name their files for successful auto-routing.
- **Multi-Task Orchestration**: Update the backend to handle multiple simultaneous processing tasks initiated by a bulk upload.

## Capabilities

### New Capabilities
- `auto-dictionary-routing`: Logic and patterns for matching raw data files to the most relevant dictionary files.

### Modified Capabilities
- `clean-data-page`: Support for multi-file selection, batch upload status tracking, and displaying auto-mapped dictionary suggestions.
- `dictionary-upload-storage`: Ensure the storage system can handle concurrent uploads and organization for batch processing.

## Impact

- Frontend: `src/pages/CleanData.tsx` and upload components.
- Backend: `backend/main.py`, `backend/core/worker.py`, and storage management.
- User Experience: Faster processing of large datasets with less manual configuration.
