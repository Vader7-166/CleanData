## Why

The project's Docker storage usage has reached an unsustainable 155GB. This is caused by inefficient Docker image builds, lack of `.dockerignore` files (leading to massive build contexts), and the accumulation of temporary files (`temp_*`, `cleaned_*`).

## What Changes

- **Docker Optimization**:
  - Create `.dockerignore` files to exclude `.venv`, `node_modules`, `__pycache__`, and large datasets from the build context.
  - Optimize `backend/Dockerfile` to use a multi-stage build or at least clean up unnecessary build dependencies.
  - Implement a cleanup mechanism for temporary processed files in `backend/main.py`.
- **System Maintenance**:
  - Provide a script/command to safely prune unused Docker layers and volumes.

## Capabilities

### New Capabilities
- `storage-management`: Automated or manual cleanup of temporary files and Docker artifacts.

### Modified Capabilities
- `build-system`: Optimize image sizes and context.

## Impact

- Significantly reduced disk usage (target reduction > 100GB).
- Faster build times due to smaller context.
- `backend/main.py` will have logic to delete files after download.
