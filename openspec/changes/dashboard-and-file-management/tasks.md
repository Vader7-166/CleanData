## 1. Database and Storage Updates

- [ ] 1.1 Update `ProcessingJob` model to include metrics (rows, cols, duration, status).
- [ ] 1.2 Add `dictionary_id` relationship to `ProcessingJob`.
- [ ] 1.3 Ensure storage directory `backend/storage/processed/` is configured.

## 2. Backend API Implementation

- [ ] 2.1 Implement GET `/api/jobs` to list all processing jobs.
- [ ] 2.2 Implement GET `/api/jobs/{id}` for detailed job stats.
- [ ] 2.3 Implement GET `/api/jobs/{id}/download` for downloading processed files.
- [ ] 2.4 Implement GET `/api/jobs/{id}/preview` with pagination/windowing support for large files.
- [ ] 2.5 Implement `cleanup_old_files()` utility function.

## 3. Frontend Dashboard and Preview

- [ ] 3.1 Implement Dashboard view with a table showing job history.
- [ ] 3.2 Implement "Detailed Info" modal/panel for job stats.
- [ ] 3.3 Create "Advanced Preview" component using an interactive grid.
- [ ] 3.4 Integrate download and delete actions into the dashboard.

## 4. Retention Policy Logic

- [ ] 4.1 Add a post-upload hook to trigger `cleanup_old_files()`.
- [ ] 4.2 Implement logic to find and remove the oldest files exceeding the limit of 10.
- [ ] 4.3 Add a UI notification/warning about the file retention policy.
