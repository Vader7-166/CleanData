## ADDED Requirements

### Requirement: Keyword Frequency Extraction
The system SHALL extract the most frequent N keywords (default 12) for each classification in the taxonomy.

#### Scenario: Keyword extraction logic
- **WHEN** processing a confirmed taxonomy group
- **THEN** the system SHALL tokenize matching raw product names and identify the top most common non-stopword tokens.

### Requirement: Taxonomy Mapping
The system SHALL ensure the generated keywords are mapped to the correct Mã HS, Dòng SP, Loại, Lớp 1, and Lớp 2 fields.

#### Scenario: CSV Formatting
- **WHEN** the final dictionary is generated
- **THEN** every row SHALL contain the 'Keyword' column followed by the 5 taxonomy columns.
