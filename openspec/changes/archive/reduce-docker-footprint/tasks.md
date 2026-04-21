## 1. Context Optimization

- [x] 1.1 Create `.dockerignore` in the project root.
- [x] 1.2 Create `backend/.dockerignore`.
- [x] 1.3 Create `frontend/.dockerignore`.

## 2. Dockerfile Optimization

- [x] 2.1 Modify `backend/Dockerfile` to combine `RUN` commands and purge build tools after use.

## 3. Backend Cleanup Logic

- [x] 3.1 Modify `backend/main.py`: Import `BackgroundTask` from `starlette.background`.
- [x] 3.2 Modify `backend/main.py`: Implement a helper function `remove_file(path: str)`.
- [x] 3.3 Modify `backend/main.py`: Update the `/upload` endpoint to return `FileResponse` with `background=BackgroundTask(remove_file, ...)`.
- [x] 3.4 Ensure the temporary `temp_` file is also removed in the background task.

## 4. Reclaiming Space

- [x] 4.1 Provide the user with the command to prune Docker system and reclaim the 155GB.
