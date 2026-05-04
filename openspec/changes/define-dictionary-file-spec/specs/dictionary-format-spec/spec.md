## ADDED Requirements

### Requirement: Mandatory CSV Structure
The dictionary file SHALL be a CSV file using `utf-8-sig` encoding and MUST contain the following columns: `Keyword`, `Dòng SP`, `Loại`, `Lớp 1`, `Lớp 2`, and `Mã HS`.

#### Scenario: Validating dictionary schema
- **WHEN** the system loads a dictionary file
- **THEN** it checks for the presence of all mandatory columns
- **THEN** it confirms the encoding is compatible with Vietnamese characters.

### Requirement: Keyword Normalization Rules
Keywords within the dictionary SHALL be normalized before being used to build the Aho-Corasick automaton. Normalization MUST include lowercasing, stripping special characters (except spaces), and collapsing multiple spaces into one.

#### Scenario: Normalizing keywords on load
- **WHEN** a dictionary row with keyword "Đèn LED, Âm Trần" is loaded
- **THEN** the system splits it into "đèn led" and "âm trần"
- **THEN** it adds both as triggers for that row's classification labels.

### Requirement: Scoring Hierarchy Support
The dictionary structure SHALL support a scoring hierarchy where certain keywords are identified as "High Value" (triggering immediate auto-approval) or "Junk" (consumed but ignored for scoring).

#### Scenario: Identifying high-value keywords
- **WHEN** a keyword in the dictionary is also present in the system's `HIGH_VALUE_KEYWORDS` list
- **THEN** matching this keyword contributes a score of 20 (or as configured) to the match result.

### Requirement: Mapping Consistency
Every dictionary entry SHALL provide a full mapping for `Dòng SP`, `Loại`, `Lớp 1`, `Lớp 2`, and `Mã HS`. If a value is unknown, it MUST be set to "không_có" rather than left blank.

#### Scenario: Assigning labels from dictionary match
- **WHEN** a product description matches a dictionary keyword
- **THEN** the system assigns all five label columns from the dictionary row to the processed record
- **THEN** any "không_có" values are treated as valid placeholders.
