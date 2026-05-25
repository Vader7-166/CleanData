## Requirements

### Requirement: Automatic Dictionary Matching
The system SHALL attempt to automatically pair uploaded raw data files with the most appropriate dictionary file based on naming patterns.

#### Scenario: Successful Pattern Match
- **GIVEN** a raw file named `7020-NK-Th12.2025.xlsx`
- **AND** a dictionary named `dict_7020_2025.xlsx` exists in storage
- **WHEN** the raw file is uploaded
- **THEN** the system SHALL suggest `dict_7020_2025.xlsx` as the dictionary for this file.

#### Scenario: Fallback for Unrecognized Patterns
- **GIVEN** a raw file with a non-standard name (e.g., `test_data.xlsx`)
- **WHEN** the file is uploaded
- **THEN** the system SHALL NOT suggest a dictionary automatically.
- **AND** the system SHALL prompt the user to select a dictionary manually.

#### Scenario: Multiple Matches
- **GIVEN** a raw file that matches multiple dictionaries
- **WHEN** the file is uploaded
- **THEN** the system SHALL suggest the most recent or highest confidence match.
