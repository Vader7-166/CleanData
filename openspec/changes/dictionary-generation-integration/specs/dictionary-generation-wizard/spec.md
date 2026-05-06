## ADDED Requirements

### Requirement: Step 1 Draft Generation
The system SHALL allow users to upload a raw Excel file and specify a product line to generate a draft taxonomy.

#### Scenario: Successful draft generation
- **WHEN** user uploads a valid raw Excel file and provides "SP THỦY TINH" as the product line
- **THEN** the system SHALL return an Excel file containing clusters with suggested category names.

### Requirement: Step 2 Finalization
The system SHALL allow users to upload a reviewed draft taxonomy and the original raw file to generate a final dictionary CSV.

#### Scenario: Final dictionary creation
- **WHEN** user uploads the reviewed draft and the original raw file
- **THEN** the system SHALL extract keywords and create a CSV file matching the DICTIONARY_SPEC.md format.
