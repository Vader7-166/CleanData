## Context

The `docker.raw` file is 155GB. In many environments (especially Mac/Windows Docker Desktop), this file represents the entire virtual disk for Docker. When contexts are large and images are built frequently without pruning, this file grows to its maximum allocated size.

## Goals / Non-Goals

**Goals:**
- Shrink the Docker image size.
- Minimize the build context.
- Prevent accumulation of temporary files in the container.

**Non-Goals:**
- Deleting user-provided datasets (in `dataset/`).
- Changing the base functionality of the PhoBERT cleaner.

## Decisions

- **.dockerignore**: Implement a global and per-service `.dockerignore`.
  - Exclude: `.git`, `.venv`, `node_modules`, `__pycache__`, `*.ipynb`, `dataset/`.
- **Backend Dockerfile Optimization**:
  - Use `python:3.10-slim` (already in use, but keep).
  - Use `--no-cache-dir` (already in use).
  - Use a single `RUN` command for apt-get to reduce layers.
  - *Crucial*: Delete build-essential after installing packages.
- **File Cleanup in FastAPI**:
  - Use Starlette's `BackgroundTask` to delete the `temp_` and `cleaned_` files immediately after they are sent to the client.
- **Docker Maintenance Command**:
  - Recommend `docker system prune -a --volumes` to the user to reclaim the 155GB.

## Risks / Trade-offs

- **[Risk]** `.dockerignore` might exclude files needed for the build.
  - **Mitigation**: Carefully verify imports.
- **[Risk]** `docker system prune -a` deletes all unused images.
  - **Mitigation**: Warn the user before they run it.
