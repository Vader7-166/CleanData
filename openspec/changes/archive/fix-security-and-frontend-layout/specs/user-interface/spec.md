## ADDED Requirements

### Requirement: Centered Layout Stability
The main UI container SHALL remain centered in the viewport on every page load and refresh.

#### Scenario: Centered on refresh
- **WHEN** the user refreshes the page
- **THEN** the `glass-container` MUST be perfectly centered horizontally and vertically

### Requirement: Robust JavaScript Execution
The frontend SHALL NOT crash if optional UI elements (like authentication inputs) are missing from the DOM.

#### Scenario: Script execution with missing inputs
- **WHEN** the `auth-section` is commented out or removed
- **THEN** the upload and processing logic SHALL still function correctly
