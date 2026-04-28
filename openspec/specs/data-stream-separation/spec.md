## ADDED Requirements

### Requirement: Separate Import and Export Data Streams
The system SHALL identify whether an uploaded dataset belongs to the import (NK) or export (XK) stream by analyzing its columns against the differences defined in `xk_nk_diff.csv`.

#### Scenario: Identify Export (XK) Data
- **WHEN** the uploaded file contains columns exclusive to the XK stream (e.g., matching the second row of `xk_nk_diff.csv`)
- **THEN** the system processes the file using the XK pipeline logic, preserving XK-specific non-predictive columns.

#### Scenario: Identify Import (NK) Data
- **WHEN** the uploaded file contains columns exclusive to the NK stream (e.g., matching the first row of `xk_nk_diff.csv`)
- **THEN** the system processes the file using the NK pipeline logic, preserving NK-specific non-predictive columns.

### Requirement: Retain Non-predictive Columns
The system SHALL append the stream-specific non-predictive columns to the final cleaned dataset alongside the model predictions.

#### Scenario: Append non-predictive columns to output
- **WHEN** data processing and prediction are complete
- **THEN** the output dataset contains both the cleaned/predicted data and the original non-predictive columns from the input data.
