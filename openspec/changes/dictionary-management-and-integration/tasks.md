## 1. Database and Storage Setup

- [ ] 1.1 Create `Dictionary` model in `backend/models.py`.
- [ ] 1.2 Create `DictionaryUsage` model in `backend/models.py`.
- [ ] 1.3 Implement database migration/initialization logic.
- [ ] 1.4 Create `backend/storage/dictionaries/` directory and ensure proper permissions.

## 2. Backend API Implementation

- [ ] 2.1 Implement POST `/api/dictionaries/upload` endpoint for CSV files.
- [ ] 2.2 Implement GET `/api/dictionaries` endpoint to list uploaded dictionaries.
- [ ] 2.3 Implement POST `/api/dictionaries/{id}/activate` endpoint to set the active dictionary.
- [ ] 2.4 Implement DELETE `/api/dictionaries/{id}` endpoint to remove a dictionary.
- [ ] 2.5 Implement GET `/api/dictionaries/stats` for usage statistics.

## 3. Frontend Implementation

- [ ] 3.1 Create Dictionary Management view/component.
- [ ] 3.2 Add upload form for dictionary files.
- [ ] 3.3 Add list display with "Activate" and "Delete" actions.
- [ ] 3.4 Add usage statistics visualization.

## 4. Pipeline Integration

- [ ] 4.1 Update `backend/core/data_cleaner.py` to fetch the currently active dictionary from the database.
- [ ] 4.2 Modify classification logic to use the active dictionary file path.
- [ ] 4.3 Add logic to record dictionary usage in `DictionaryUsage` after successful processing.
- [ ] 4.4 Update `extracted_pipeline.py` if necessary to support dynamic dictionary loading.
