## Why

The backend was failing to start due to missing `protobuf` and `sentencepiece` dependencies required by the PhoBERT tokenizer. Additionally, a `bcrypt` version mismatch was causing `passlib` to crash during user creation, forcing a temporary bypass of admin user initialization.

## What Changes

- **Dependency Updates**:
  - Add `protobuf` and `sentencepiece` to `backend/requirements.txt`.
  - Pin `bcrypt` to a compatible version (3.2.2) to resolve `passlib` issues.
- **Backend Logic**:
  - Re-enable admin user creation in `backend/main.py`'s `startup_event`.

## Capabilities

### Modified Capabilities
- `build-system`: Dependency management and image stability.

## Impact

- Backend will now successfully load the PhoBERT tokenizer on startup.
- Admin user will be correctly initialized in the database, allowing for accurate history tracking during file uploads.
