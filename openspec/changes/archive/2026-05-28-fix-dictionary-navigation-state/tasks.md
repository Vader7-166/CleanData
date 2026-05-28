## 1. Backend API Updates

- [x] 1.1 Create `DELETE /api/dictionary/{filename}` endpoint in the backend to delete physical files from `Create_Dictionary/output/` or `Create_Dictionary/final/`.

## 2. Frontend State Persistence

- [x] 2.1 Refactor the main file upload/selection state to be held in a global context (e.g., React Context) or high-level component above the router so it persists across page navigations.
- [x] 2.2 Update Clean Data and Dictionary Generation pages to consume this shared state instead of local component state.

## 3. Frontend UI Updates

- [x] 3.1 Update the raw file input element in the Dictionary Generation wizard to include the `multiple` attribute and handle array of selected files.
- [x] 3.2 Add a "Delete" button with a confirmation modal to the Dictionary Management page cards/table.
- [x] 3.3 Connect the "Delete" button to the new backend DELETE endpoint and update the UI list upon success.
