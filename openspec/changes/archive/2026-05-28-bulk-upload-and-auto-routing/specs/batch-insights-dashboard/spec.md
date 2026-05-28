## ADDED Requirements

### Requirement: Consolidated Read-Only Preview
The system SHALL display an aggregated read-only preview of processed rows across all files in a batch.

#### Scenario: Displaying batch preview
- **GIVEN** a Batch contains two processed files: `fileA.xlsx` (10 rows) and `fileB.xlsx` (15 rows)
- **WHEN** the user opens the Batch Preview
- **THEN** the system SHALL render a unified grid with a `Tên file nguồn` column identifying each row's source file

### Requirement: Review Status Filter
The system SHALL support filtering to display only rows marked as `Cần kiểm tra` across all files.

#### Scenario: Filtering rows needing review
- **GIVEN** a batch contains 1,000 processed rows, where 5 are marked `Cần kiểm tra`
- **WHEN** the user enables the "Chỉ hiện dòng cần duyệt" filter
- **THEN** the system SHALL display only those 5 rows

### Requirement: Quick Market Insights Charts
The system SHALL render built-in mini-charts providing instant insights into market distribution.

#### Scenario: Visualizing product lines and ratios
- **GIVEN** a successfully processed batch
- **WHEN** the user views the batch insights section
- **THEN** the system SHALL render a doughnut chart of `Dòng SP` distribution
- **AND** a pie chart of `NC` vs `LK` ratio
- **AND** a bar chart ranking top 5 companies by total `Giá trị`
