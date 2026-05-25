## 1. Research and Identification

- [x] 1.1 Locate the exact component and CSS responsible for the file details modal in `frontend/src/pages/Dashboard.tsx` or its child components.
- [x] 1.2 Identify the specific elements where white-on-white text occurs.

## 2. UI Implementation

- [x] 2.1 Apply `max-h-[90vh]` and `overflow-y-auto` to the modal container to fix overflow issues.
- [x] 2.2 Update text color classes to ensure readability (e.g., use `text-slate-900`).
- [x] 2.3 Verify and fix the close button visibility and click handler.
- [x] 2.4 Ensure clicking the backdrop or pressing ESC closes the modal.

## 3. Verification

- [ ] 3.1 Test the modal with a large dataset to ensure scrolling works.
- [ ] 3.2 Test the modal on different screen sizes to ensure responsiveness.
- [ ] 3.3 Verify text readability across all sections of the modal.
