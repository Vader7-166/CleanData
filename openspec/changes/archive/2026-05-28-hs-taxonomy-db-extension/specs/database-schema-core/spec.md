## MODIFIED Requirements

### Requirement: HS Code to Industry and Classification Mapping (`HSTaxonomy`)
The system SHALL maintain a database table mapping HS codes/prefixes to their corresponding Product Line (`Dòng SP`), Industry Category (`Lớp 1`), Component Classification (`Loại` - NC/LK), and creation metadata.

#### Scenario: Taxonomy and Type Lookup by HS Code Prefix
- **GIVEN** an HS code `8539.52.10`
- **AND** an `HSTaxonomy` record exists for prefix `85395210` with:
  - `dong_sp`: "SP ĐÈN/BÓNG ĐÈN"
  - `industry_name` (Lớp 1): "Bóng đèn LED - đầu đèn ren xoáy"
  - `default_type` (Loại): "NC"
- **WHEN** the system generates a dictionary draft or cleans a file containing this HS code
- **THEN** the system SHALL map the columns to match these database values.

#### Scenario: Bulk Taxonomy Import
- **WHEN** an administrator uploads a CSV/Excel file containing `hs_code_prefix`, `dong_sp`, `industry_name`, and `default_type` columns
- **THEN** the system SHALL populate the `HSTaxonomy` table, overwriting or adding the records.

#### Scenario: Asynchronous Online Crawler Lookup
- **WHEN** a new HS code is processed that is not found in the `HSTaxonomy` table
- **THEN** the system SHALL launch an online lookup request to scrape public customs directories for the HS code description.
- **AND IF** the crawler resolves the description
- **THEN** the system SHALL parse the text, assign a default type (`NC` or `LK`), and save it to the DB.

#### Scenario: Step 1 Manual UI Interception (Option 1)
- **GIVEN** a file with unknown HS codes that the database and online crawler fail to resolve
- **WHEN** the user initiates Step 1 of the Dictionary Generator Wizard
- **THEN** the wizard SHALL pause and display a form prompting the user to manually enter `Dòng sản phẩm`, `Lớp 1`, and `Loại` (NC/LK) for each unknown HS code.
- **AND WHEN** the user submits the form
- **THEN** the system SHALL persist these records to `HSTaxonomy` and proceed to generate the dictionary draft.
