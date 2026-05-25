## Requirements

### Requirement: HS Taxonomy Management Interface
The system SHALL provide a dedicated page for managing HS code to industry mappings.

#### Scenario: List All Mappings
- **WHEN** a user navigates to the HS Taxonomy Management page
- **THEN** the system SHALL display a table containing all records from the `HSTaxonomy` table.
- **AND** the table SHALL include columns for: HS Code Prefix, Industry Name, and Description.

#### Scenario: Add a New Mapping
- **WHEN** the user clicks the "Add New" button
- **THEN** a form SHALL be displayed to enter the HS Code Prefix, Industry Name, and Description.
- **AND** upon submission, the record SHALL be saved and the table updated.

#### Scenario: Edit an Existing Mapping
- **WHEN** the user clicks "Edit" on a specific row
- **THEN** the system SHALL allow modifying the Industry Name and Description.
- **AND** upon saving, the changes SHALL be reflected in the database.

#### Scenario: Delete a Mapping
- **WHEN** the user clicks "Delete" on a specific row
- **THEN** the system SHALL ask for confirmation.
- **AND** upon confirmation, the record SHALL be removed from the database.
