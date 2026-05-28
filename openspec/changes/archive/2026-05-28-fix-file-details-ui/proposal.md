## Why

Users are currently unable to effectively view file details because the modal or detail view has several UI bugs: content overflows the screen boundaries, font colors clash with the background (white on white), and the close button is either missing or non-functional. These issues hinder the ability to review processed data results.

## What Changes

- **Fix UI Overflow**: Ensure the file details modal/view is responsive and fits within the viewport, using scrollbars where necessary.
- **Improve Text Visibility**: Update font colors to ensure high contrast against the background (fixing the white-on-white issue).
- **Fix Modal Control**: Ensure the close button is visible and correctly dismisses the detail view.

## Capabilities

### New Capabilities
- None

### Modified Capabilities
- `file-history-dashboard`: Update the requirements for the file details modal to ensure visibility, accessibility, and proper containment within the UI.

## Impact

- Frontend: `src/pages/Dashboard.tsx` (or wherever file details are rendered).
- UI Components: Modals or detail view components.
