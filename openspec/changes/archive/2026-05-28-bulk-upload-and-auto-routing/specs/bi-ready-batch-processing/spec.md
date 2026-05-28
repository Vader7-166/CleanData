## ADDED Requirements

### Requirement: Multi-File Batch Upload & Sequential Queueing
The system SHALL support uploading multiple raw Excel/CSV files simultaneously under a single batch, and queue their execution sequentially on the backend.

#### Scenario: Queueing multiple uploaded files
- **GIVEN** a user selects three raw files for upload
- **WHEN** the user submits the upload request
- **THEN** the system SHALL create a single Batch containing three Jobs
- **AND** the backend SHALL process them one by one, keeping other jobs in `Pending` status until the preceding job completes

### Requirement: Transaction Type Auto-Detection
The system SHALL detect whether a raw file represents import or export transactions and append a `Loại giao dịch` column.

#### Scenario: Import transaction detection
- **GIVEN** an uploaded file containing the column `VN_Importer`
- **WHEN** the system analyzes the file schema
- **THEN** the resulting dataset SHALL contain a column `Loại giao dịch` with all rows set to `Nhập khẩu`

#### Scenario: Export transaction detection
- **GIVEN** an uploaded file containing the column `VN_Exporter`
- **WHEN** the system analyzes the file schema
- **THEN** the resulting dataset SHALL contain a column `Loại giao dịch` with all rows set to `Xuất khẩu`

#### Scenario: Frontend override
- **GIVEN** the system has auto-detected the transaction type
- **WHEN** the user changes the toggle to a different type before processing
- **THEN** the system SHALL use the user's manual selection instead of the auto-detected value

### Requirement: BI-Ready Date Standardization
The system SHALL preserve the full original date as ISO format and provide a separate month column for pivot analysis.

#### Scenario: Standardizing date with full information
- **GIVEN** a raw file with a `Date` column containing `2025-12-25`
- **WHEN** the cleaning pipeline runs
- **THEN** the `Ngày` column SHALL contain `2025-12-25`
- **AND** a `Tháng` column SHALL contain `12`

#### Scenario: Fallback when only month is available
- **GIVEN** a raw file with a `Month` column but no parseable `Date` column
- **WHEN** the cleaning pipeline runs
- **THEN** the `Ngày` column SHALL be empty
- **AND** the `Tháng` column SHALL contain the extracted month number

### Requirement: BI-Ready Numeric Sanitization
The system SHALL clean numeric columns to pure decimal floats, removing all formatting characters.

#### Scenario: Sanitizing formatted currency values
- **GIVEN** a `Total_Value_USD` value of `1,250.50 USD`
- **WHEN** the cleaning pipeline runs
- **THEN** the `Giá trị` column SHALL contain the float `1250.5`

### Requirement: Column Header Unification
The system SHALL normalize all output column headers to consistent Vietnamese names and remove duplicate pandas suffixes.

#### Scenario: Renaming English headers
- **WHEN** the cleaning pipeline generates the output
- **THEN** `Method_of_Payment` SHALL be renamed to `Phương thức thanh toán`
- **AND** any column ending in `.1` suffix SHALL be renamed or removed

### Requirement: Flexible Download Options
The system SHALL support multiple download formats for a completed batch.

#### Scenario: Downloading individual file
- **WHEN** the user clicks download on a specific job within a batch
- **THEN** the system SHALL serve the individual cleaned file

#### Scenario: Downloading merged Excel
- **WHEN** the user clicks "Download Merged" on a batch
- **THEN** the system SHALL serve a single Excel file combining all cleaned files with added `Tên file nguồn` and `Loại giao dịch` columns

#### Scenario: Downloading ZIP archive
- **WHEN** the user clicks "Download ZIP" on a batch
- **THEN** the system SHALL serve a ZIP archive containing all individual cleaned files
