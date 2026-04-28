## Context

The current application lacks a robust way to manage dictionaries for data cleaning. Users must manually replace a file on disk to change classification behavior. The backend is built with FastAPI and SQLAlchemy (SQLite).

## Goals / Non-Goals

**Goals:**
- Provide a centralized repository for dictionary files.
- Enable dynamic selection of the active dictionary for the cleaning pipeline.
- Maintain a history of which dictionary was used for each processing job.

**Non-Goals:**
- Editing dictionary contents within the application UI (only upload/delete).
- Multi-user isolation for dictionaries (global availability for now).

## Decisions

### Storage Strategy
Dictionary files will be stored in a dedicated directory `backend/storage/dictionaries/`.
**Rationale:** Keeps data separate from code and allows for easy backup/management of files.

### Database Schema
Create two new models:
1. `Dictionary`: Stores metadata about uploaded dictionaries (`id`, `filename`, `display_name`, `upload_date`, `is_active`).
2. `ProcessingJob` (or similar): Tracks files processed, linking to the `Dictionary` used.
**Rationale:** Enables structured querying of available dictionaries and audit trail for processing results.

### Active Dictionary Management
Only one dictionary can be marked `is_active=True` at a time. When a new one is activated, the previous one is deactivated.
**Rationale:** Simplifies the pipeline logic by having a single source of truth for the classification pass.

## Risks / Trade-offs

- **Risk:** File system and database getting out of sync (e.g., file deleted but DB record remains).
  - **Mitigation:** Wrap deletion in a transaction/utility that handles both.
- **Risk:** Large dictionary files consuming server space.
  - **Mitigation:** Implement basic file size limits on upload.
- **Trade-off:** Global "active" dictionary means concurrent jobs will use the same dictionary. This is acceptable for the current prototype phase.
