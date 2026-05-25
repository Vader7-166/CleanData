## 1. Backend Implementation

- [ ] 1.1 Update the upload API in `backend/main.py` to support `List[UploadFile]`.
- [ ] 1.2 Implement the `AutoRoutingService` in `backend/core/routing.py` with regex patterns for filename matching.
- [ ] 1.3 Create an endpoint to list available dictionaries with their metadata (extracted HS code/year).
- [ ] 1.4 Update the task creation logic to handle a list of file-dictionary pairs.

## 2. Frontend Implementation

- [ ] 2.1 Update the file upload component in `src/pages/CleanData.tsx` to allow `multiple` selection.
- [ ] 2.2 Implement a "Review & Pair" step in the UI after files are uploaded but before processing starts.
- [ ] 2.3 Display suggested dictionaries and allow manual overrides.
- [ ] 2.4 Add a batch processing button that triggers multiple API calls or a single batch API call.

## 3. UI/UX Improvements

- [ ] 3.1 Add a "Naming Convention Guide" tooltip or modal to help users name files correctly for auto-routing.
- [ ] 3.2 Show processing progress for each file in the batch list.

## 4. Verification

- [ ] 4.1 Test uploading multiple files with various naming patterns (matching and non-matching).
- [ ] 4.2 Verify that the correct dictionaries are suggested.
- [ ] 4.3 Verify that multiple processing tasks are created and run successfully.
