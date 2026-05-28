## Context

Currently, the AI Dictionary Generation process is fully synchronous from the frontend's perspective, though it runs in an `asyncio.to_thread` on the backend. If the user navigates away, the HTTP request is aborted by the browser, but the thread keeps running on the backend without any way for the user to retrieve the result or view its progress. Furthermore, dictionary management currently only supports activating/managing one dictionary at a time.

## Goals / Non-Goals

**Goals:**
- Provide a robust way for the frontend to poll for generation progress.
- Allow users to navigate away from the wizard and return to see the ongoing generation job.
- Enable users to select and activate multiple dictionaries simultaneously on the management page.

**Non-Goals:**
- We will not implement a full asynchronous message queue (e.g., Celery/Redis) to keep the deployment simple.
- We will not persist generation progress across backend server restarts.

## Decisions

1. **Background Job Tracking via In-Memory Store & Polling:**
   - **Decision:** Instead of a long-polling HTTP request that blocks, the `step1` endpoint will immediately return a `job_id`. The backend will maintain an in-memory dictionary `ACTIVE_GEN_JOBS = {}` tracking the progress (e.g., `{ status: "processing", progress: "Batch 1/5", result_file: null }`).
   - **Rationale:** An in-memory store avoids the need for external dependencies like Redis. While it won't survive a server restart, it perfectly solves the "frontend navigation timeout" issue.
   - **Frontend:** The UI will poll `GET /api/dictionaries/generate/status/{job_id}` every 2 seconds. The `job_id` will be saved in `localStorage` or `FileContext` so it persists across navigations.

2. **Progress Indicator Updates:**
   - **Decision:** The `DictionaryGenerator` core class will accept a callback function to report its progress, updating the in-memory job store.
   - **Rationale:** DeepSeek LLM clustering is heavily batched. Reporting progress at the batch level provides clear visibility without excessive overhead.

3. **Multi-Dictionary Management UI:**
   - **Decision:** Add checkboxes to the Dictionary cards in `Dictionary.tsx`. Provide a bulk "Activate Selected" button.
   - **Rationale:** Standard UX pattern that is easy to implement. The frontend will iterate and call the existing activation endpoints, or we will introduce a bulk activate endpoint if necessary.

## Risks / Trade-offs

- **Risk:** Memory leaks if jobs are never cleared from the in-memory dictionary.
  - **Mitigation:** The backend will automatically delete the job entry 10 minutes after it completes or errors out, or immediately once the frontend successfully fetches the final draft file.
- **Risk:** Load balancer timeouts (if applicable).
  - **Mitigation:** Since we are moving to a polling architecture, the initial POST request returns immediately, effectively eliminating the risk of long-lived HTTP connection timeouts.
