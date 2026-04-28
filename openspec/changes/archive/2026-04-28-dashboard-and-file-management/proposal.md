## Why

Currently, the application lacks a central place to manage files and monitor the history of processing tasks. Users cannot easily revisit past uploads, see detailed metrics of their files, or enjoy a rich preview experience. Implementing a dashboard and a robust file management system will significantly improve user experience, data visibility, and system maintenance by enforcing storage limits.

## What Changes

- Create a central Dashboard view for managing all file-related activities.
- Implement file listing with capabilities to download or delete past uploads.
- Enhance the file preview to support larger datasets (>100 lines), all columns, and an excel-like UI.
- Add detailed file metadata tracking (row/column counts, dictionary used, processing duration, error status).
- Enforce a 10-file retention policy per user (or globally for now) to manage storage space.
- Integrate pipeline monitoring details directly into the file management history.

## Capabilities

### New Capabilities
- `file-history-dashboard`: A central interface to list, manage, and view the status of all uploaded and processed files.
- `file-retention-policy`: Automatic management of stored files to keep only the 10 most recent entries.

### Modified Capabilities
- `excel-preview-ui`: Upgrade from a basic 100-row preview to an advanced, excel-style preview supporting all columns and larger row counts.
- `pipeline-monitoring-ui`: Expand from real-time logging to persistent detailed statistics for each processing job (dictionary used, row/column counts, processing time).

## Impact

- Backend: Updates to file storage logic, new endpoints for file management and detailed stats, background cleanup for retention policy.
- Frontend: Major UI overhaul with a new Dashboard, improved Preview component, and detailed file info panels.
- Database: Expansion of file-related models to store metrics and metadata.
