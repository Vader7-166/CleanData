## ADDED Requirements

### Requirement: Global Process Pool Executor
The backend system SHALL initialize and maintain a single global `ProcessPoolExecutor` (or equivalent worker queue) for asynchronous multi-processing tasks to prevent process fork bombing when handling multiple concurrent web requests.

#### Scenario: Multiple Concurrent Uploads
- **WHEN** multiple users upload files and trigger the data cleaning pipeline concurrently
- **THEN** the backend assigns chunk processing tasks to the existing global worker pool instead of creating a new set of processes per request, maintaining stable memory and CPU consumption.
