## Requirements

### Requirement: HS Taxonomy Management Interface
The system SHALL provide a dedicated administration page for managing HS code to industry taxonomy mappings.

#### Scenario: List All Mappings
- **WHEN** a user navigates to the HS Taxonomy Management page
- **THEN** the system SHALL display a table containing all records from the `HSTaxonomy` table.
- **AND** the table SHALL include columns for: HS Code Prefix, Dòng sản phẩm, Lớp 1 (Industry Name), Phân loại (Loại), Source, and Updated At.

#### Scenario: Add a New Mapping
- **WHEN** the user clicks the "Add New Mapping" button
- **THEN** a form SHALL be displayed to enter the HS Code Prefix, select the Dòng sản phẩm (from predefined list/dropdown), enter Lớp 1 (Industry Name), select the Phân loại (Loại: NC or LK), and enter a Description.
- **AND** upon submission, the record SHALL be saved to the DB with source set as `user_input` and the table updated.

#### Scenario: Edit an Existing Mapping
- **WHEN** the user clicks "Edit" on a specific row
- **THEN** the system SHALL display a form allowing the user to modify the Dòng sản phẩm, Lớp 1, Phân loại (Loại), and Description.
- **AND** upon saving, the changes SHALL be updated in the database.

#### Scenario: Delete a Mapping
- **WHEN** the user clicks "Delete" on a specific row
- **THEN** the system SHALL ask for confirmation.
- **AND** upon confirmation, the record SHALL be removed from the database.
