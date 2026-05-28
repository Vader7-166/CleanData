## 1. Backend In-Memory Job Tracking

- [x] 1.1 Add an in-memory dictionary `ACTIVE_GEN_JOBS = {}` in `backend/main.py` to hold generation job states.
- [x] 1.2 Refactor `POST /api/dictionaries/generate/step1` to generate a `job_id`, initialize the job state, and run `generate_draft_taxonomy` as a `BackgroundTask` instead of awaiting it directly.
- [x] 1.3 Create `GET /api/dictionaries/generate/status/{job_id}` endpoint to allow the frontend to poll for progress.
- [x] 1.4 Create `GET /api/dictionaries/generate/download/{job_id}` endpoint to download the finalized Excel draft once the job status is "done".

## 2. Backend Progress Reporting

- [x] 2.1 Update `generate_draft_taxonomy` in `backend/core/dict_generator.py` to accept a `progress_callback` function.
- [x] 2.2 Trigger `progress_callback` within the LLM clustering loops to report granular progress (e.g., "Batch X of Y processed").

## 3. Frontend Generation Wizard Updates

- [x] 3.1 Update `DictionaryGeneratorWizard.tsx` to receive the `job_id` from Step 1 and store it persistently using `usePersistedState`.
- [x] 3.2 Implement a polling mechanism (e.g., `setInterval`) in the Wizard to fetch job status every 2 seconds if an active `job_id` exists.
- [x] 3.3 Add a visual progress UI (e.g., a progress bar or status text) showing the real-time completion state of the AI generation.
- [x] 3.4 Handle the "done" state by automatically triggering the draft download from the new backend download endpoint.

## 4. Multi-Dictionary Management

- [x] 4.1 Update `Dictionary.tsx` to render checkboxes next to each dictionary card/row in the management list.
- [x] 4.2 Add a "Bulk Activate" button that iterates and calls the activation API for all selected dictionary IDs.
