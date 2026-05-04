## 1. Database and Storage Setup

- [x] 1.1 Create `Dictionary` model in `backend/models.py`.
- [x] 1.2 Create `DictionaryUsage` model in `backend/models.py`.
- [x] 1.3 Implement database migration/initialization logic.
- [x] 1.4 Create `backend/storage/dictionaries/` directory and ensure proper permissions.

## 2. Backend API Implementation

- [x] 2.1 Implement POST `/api/dictionaries/upload` endpoint for CSV files.
- [x] 2.2 Implement GET `/api/dictionaries` endpoint to list uploaded dictionaries.
- [x] 2.3 Implement POST `/api/dictionaries/{id}/activate` endpoint to set the active dictionary.
- [x] 2.4 Implement DELETE `/api/dictionaries/{id}` endpoint to remove a dictionary.
- [x] 2.5 Implement GET `/api/dictionaries/stats` for usage statistics.

## 3. Frontend Implementation

- [x] 3.1 Create Dictionary Management view/component.
- [x] 3.2 Add upload form for dictionary files.
- [x] 3.3 Add list display with "Activate" and "Delete" actions.
- [x] 3.4 Add usage statistics visualization.

## 4. Pipeline Integration

- [x] 4.1 Update `backend/core/data_cleaner.py` to fetch the currently active dictionary from the database.
- [x] 4.2 Modify classification logic to use the active dictionary file path.
- [x] 4.3 Add logic to record dictionary usage in `DictionaryUsage` after successful processing.
- [x] 4.4 Update `extracted_pipeline.py` if necessary to support dynamic dictionary loading.
