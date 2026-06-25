## ADDED Requirements

### Requirement: HS taxonomy database lookup in pipeline

The system SHALL query the HSTaxonomy database table for each row's `Mã HS` using longest-prefix matching (trying full code, then 10, 8, 6, 4 digits) before running dictionary or AI classification.

#### Scenario: Exact prefix match found
- **WHEN** `Mã HS = "85391010"` is looked up in HSTaxonomy
- **THEN** the system finds the matching record with `hs_code_prefix = "853910"` or `"8539"`
- **AND** returns `dong_sp`, `industry_name`, and `default_type` from the matched record

#### Scenario: No match in taxonomy
- **WHEN** `Mã HS` is not found in HSTaxonomy
- **THEN** no pre-classification is applied
- **AND** the row proceeds to dictionary matching

### Requirement: Pre-fill threshold based on dictionary frequency

The system SHALL only pre-fill classification fields when the corresponding dictionary row has `Số lượng SP > 100`, indicating high frequency and reliability of the classification.

#### Scenario: High-frequency HS code
- **WHEN** a matched HSTaxonomy record's HS prefix has dict rows with `Số lượng SP > 100`
- **THEN** `Dòng SP` and `Loại` are pre-filled with the taxonomy/dict values
- **AND** the row is skipped for dict matching on those fields

#### Scenario: Low-frequency HS code
- **WHEN** a matched HSTaxonomy record's HS prefix has dict rows with `Số lượng SP <= 100`
- **THEN** pre-classification is NOT applied
- **AND** the full dict → AI chain runs normally

### Requirement: Partial pre-fill — only confident levels

The HS pre-classification SHALL only fill `Dòng SP` and `Loại` (the two highest, most reliable classification levels). `Lớp 1` and `Lớp 2` SHALL remain for dict/AI classification.

#### Scenario: Pre-fill top levels only
- **WHEN** HS-based pre-classification is triggered
- **THEN** `Dòng SP` is set from taxonomy match
- **AND** `Loại` is set from taxonomy `default_type` or dict match
- **AND** `Lớp 1` and `Lớp 2` remain empty for subsequent classification
