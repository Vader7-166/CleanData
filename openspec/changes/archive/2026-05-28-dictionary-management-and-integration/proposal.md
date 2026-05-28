## Why

The current data cleaning pipeline uses a static dictionary file (`dictv3.csv`) for product classification. This lack of flexibility prevents users from updating dictionary entries or using specialized dictionaries for different product types without modifying the source code or file system. Adding dictionary management will allow for more dynamic and accurate processing by enabling users to upload, select, and track the usage of various dictionaries tailored to their specific needs.

## What Changes

- Implement a new API endpoint and frontend interface for uploading dictionary files.
- Create a storage system to persist uploaded dictionary files.
- Develop a dictionary management UI to list, view, and select active dictionaries.
- Update the classification logic to utilize the user-selected dictionary instead of a hardcoded file.
- Implement a tracking mechanism to record which dictionary was used for each processed file.
- Provide a summary of dictionary usage statistics.

## Capabilities

### New Capabilities
- `dictionary-upload-storage`: Capability to upload and persist dictionary files securely.
- `dictionary-management-ui`: A user interface to list, manage, and select from uploaded dictionaries.
- `dictionary-usage-statistics`: A system to track and display metrics on how dictionaries are being utilized across different processing jobs.

### Modified Capabilities
- `dictionary-filtering`: Update requirements to move away from a hardcoded `dictv3.csv` to using a dynamically selected dictionary from the management system.

## Impact

- Backend: New endpoints in `main.py`, database schema updates in `models.py`/`database.py` for dictionary metadata.
- Frontend: New UI components for dictionary management and integration into the processing workflow.
- Pipeline: `data_cleaner.py` and `extracted_pipeline.py` will need to accept a dictionary parameter or fetch the active dictionary configuration.
