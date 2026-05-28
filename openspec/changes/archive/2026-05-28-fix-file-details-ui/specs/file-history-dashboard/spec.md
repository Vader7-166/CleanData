## MODIFIED Requirements

### Requirement: Enhanced File Details Modal
The system SHALL provide a file details view that is accessible, readable, and manageable.

#### Scenario: View File Details without Overflow
- **WHEN** a user opens the details for a processed file with many rows
- **THEN** the modal SHALL NOT exceed 90% of the viewport height.
- **AND** the modal SHALL provide internal scrolling for the content.

#### Scenario: Text Readability
- **WHEN** any text is displayed within the file details modal
- **THEN** the system SHALL ensure the text color has a contrast ratio of at least 4.5:1 against the background (WCAG AA).
- **AND** specifically, no white text SHALL be displayed on a white background.

#### Scenario: Modal Closure
- **WHEN** the file details modal is open
- **THEN** a visible close button SHALL be provided at the top-right corner.
- **AND** the modal SHALL close when the user clicks the close button, clicks the backdrop, or presses the ESC key.
