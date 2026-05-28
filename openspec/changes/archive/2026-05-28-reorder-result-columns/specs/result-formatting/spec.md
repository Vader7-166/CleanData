## ADDED Requirements

### Requirement: Output Column Reordering
The system SHALL reorder the columns of the generated output file to match a predefined standard based on `sample.csv`.

#### Scenario: Reordering successful
- **WHEN** the output data is prepared for export
- **THEN** the columns are ordered exactly as they appear in the sample format

### Requirement: Metadata Columns Placement
The system MUST place the "Trạng thái" and "Độ tự tin" columns at the very end of the output file.

#### Scenario: Metadata at the end
- **WHEN** the output file is generated
- **THEN** the last two columns of the file are exactly "Trạng thái" and "Độ tự tin" in that order