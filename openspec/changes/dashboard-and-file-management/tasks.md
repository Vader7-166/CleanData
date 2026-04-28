## 1. Database and Storage Updates

- [x] 1.1 Update `ProcessingJob` model to include metrics (rows, cols, duration, status).
- [x] 1.2 Add `dictionary_id` relationship to `ProcessingJob`.
- [x] 1.3 Ensure storage directory `backend/storage/processed/` is configured.

## 2. Backend API Implementation

- [x] 2.1 Implement GET `/api/jobs` to list all processing jobs.
- [x] 2.2 Implement GET `/api/jobs/{id}` for detailed job stats.
- [x] 2.3 Implement GET `/api/jobs/{id}/download` for downloading processed files.
- [x] 2.4 Implement GET `/api/jobs/{id}/preview` with pagination/windowing support for large files.
- [x] 2.5 Implement `cleanup_old_files()` utility function.

## 3. Frontend Dashboard and Preview

- [x] 3.1 Implement Dashboard view with a table showing job history.
- [x] 3.2 Implement "Detailed Info" modal/panel for job stats.
- [x] 3.3 Create "Advanced Preview" component using an interactive grid.
- [x] 3.4 Integrate download and delete actions into the dashboard.

## 4. Retention Policy Logic

- [x] 4.1 Add a post-upload hook to trigger `cleanup_old_files()`.
- [x] 4.2 Implement logic to find and remove the oldest files exceeding the limit of 10.
- [x] 4.3 Add a UI notification/warning about the file retention policy.
