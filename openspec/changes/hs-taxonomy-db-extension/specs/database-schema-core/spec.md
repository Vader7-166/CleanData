## MODIFIED Requirements

### Requirement: HS Code to Industry Mapping (HS_TAXONOMY)
The system SHALL maintain a database of mappings between HS codes and industry categories.

#### Scenario: Industry Lookup by HS Code
- **GIVEN** an HS code `7020.10.00`
- **AND** a taxonomy record exists for prefix `7020` as "Glassware"
- **WHEN** the system processes a file with this HS code
- **THEN** the system SHALL be able to associate the record with the "Glassware" industry.

#### Scenario: Bulk Taxonomy Import
- **WHEN** an administrator uploads a CSV/Excel file with `hs_code_prefix` and `industry_name` columns
- **THEN** the system SHALL populate the `HSTaxonomy` table with these mappings.

#### Scenario: Flexible Prefix Matching
- **WHEN** looking up an industry for an HS code
- **THEN** the system SHALL match the longest available prefix in the `HSTaxonomy` table.
