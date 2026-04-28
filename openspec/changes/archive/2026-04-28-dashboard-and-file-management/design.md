## Context

The current system is ephemeral - once a file is processed and downloaded, it is effectively "lost" from the UI. There is no historical tracking or easy way to re-examine results.

## Goals / Non-Goals

**Goals:**
- Provide a persistent Dashboard for file management.
- Improve data visualization with an advanced previewer.
- Automate storage cleanup.

**Non-Goals:**
- Supporting more than 10 files (strict limit).
- Multi-user authentication (single-user dashboard for now).

## Decisions

### Model Expansion
Update the `File` model (or create `ProcessingJob`) to include:
- `total_rows`, `total_columns`
- `dictionary_id` (foreign key)
- `processing_time_ms`
- `status` (PENDING, SUCCESS, FAILED)
- `error_message`

### Advanced Preview Implementation
Instead of loading the entire file, the backend will provide a paginated or windowed view of the processed Excel data. The frontend will use a high-performance grid component (like `ag-grid` or a simplified custom implementation) to handle smooth scrolling.

### Retention Worker
Implement a hook after each successful upload that checks the total count of files in the database. If count > 10, it triggers a cleanup function that removes the oldest file entry and its physical file from disk.

## Risks / Trade-offs

- **Risk:** Deleting files might be unexpected if the user didn't notice the 10-file limit.
  - **Mitigation:** Display a clear warning on the dashboard about the 10-file limit.
- **Trade-off:** High-performance preview might increase backend memory usage if not implemented carefully with streaming/windowed reads.
