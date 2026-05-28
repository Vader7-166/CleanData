## ADDED Requirements

### Requirement: Memory-Safe Upload Streaming
The system SHALL process bulk file uploads by reading the data in chunks (or sequentially line-by-line) and appending it to a single temporary master file on disk, preventing Out-Of-Memory errors from pandas DataFrame concatenation.

#### Scenario: Multiple large files uploaded
- **WHEN** a user uploads multiple large CSV/Excel files simultaneously
- **THEN** the backend processes each file stream and incrementally appends rows to a `merged_job_<id>.csv` on disk without loading all data into RAM at once.

### Requirement: Single Pipeline Execution
The Data Cleaner Pipeline SHALL execute once per batch on the merged temporary master file rather than invoking the pipeline separately for every individual raw file.

#### Scenario: Batch Processing Trigger
- **WHEN** all files in a batch have been merged into the master temporary file
- **THEN** the system triggers the asynchronous multiprocessing pipeline on the single master file, which produces a single unified output file.
