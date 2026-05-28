## ADDED Requirements

### Requirement: Dictionary HS Code Metadata
The `Dictionary` model SHALL store a `hs_code_prefixes` field containing the comma-separated list of 4-digit HS code prefixes that the dictionary covers.

#### Scenario: Auto-populating hs_code_prefixes on dictionary generation
- **GIVEN** a new dictionary is generated via the Dictionary Generator wizard from a raw file
- **WHEN** the dictionary CSV is finalized and saved
- **THEN** the system SHALL scan the `Mã HS` column of the output CSV, extract unique 4-digit prefixes, and store them in the `hs_code_prefixes` field

#### Scenario: Migrating existing dictionaries
- **GIVEN** existing dictionaries that have no `hs_code_prefixes` metadata
- **WHEN** a migration script runs
- **THEN** the system SHALL read each dictionary CSV file from storage, extract unique 4-digit HS prefixes from the `Mã HS` column, and populate the field

### Requirement: HS Code-Based Dictionary Selection
The system SHALL select the best dictionary for a raw file by matching the HS codes present in the file against the `hs_code_prefixes` metadata on Dictionary records.

#### Scenario: Matching file to specific dictionary
- **GIVEN** a raw file containing rows with HS codes `85395210`, `85395220`, and `94051110`
- **AND** Dictionary A has `hs_code_prefixes` = `"8539,9405"` and Dictionary B has `hs_code_prefixes` = `"7020"`
- **WHEN** the system determines which dictionary to use
- **THEN** the system SHALL select Dictionary A (2 prefix matches vs 0 for Dictionary B)

#### Scenario: Fallback to active dictionary
- **GIVEN** a raw file whose HS codes do not match any dictionary's `hs_code_prefixes`
- **WHEN** the system determines which dictionary to use
- **THEN** the system SHALL fall back to the user's globally active dictionary
