## ADDED Requirements

### Requirement: Parallel Dictionary Matching
The system SHALL execute the dictionary mapping phase concurrently across multiple processes or threads to minimize execution time on large datasets.

#### Scenario: Processing large dataset dictionary matching
- **WHEN** a dataset with thousands of rows is processed
- **THEN** the dataframe is split into chunks and processed in parallel
- **THEN** the output dataframe contains the exact same dictionary matching labels as sequential processing

### Requirement: Concurrent AI Batch Processing
The system SHALL execute AI model inference batches concurrently using asynchronous programming up to a configured concurrency limit.

#### Scenario: Executing multiple AI fallback chunks
- **WHEN** there are multiple chunks of data falling back to AI inference
- **THEN** the system dispatches them concurrently via `asyncio.gather`
- **THEN** the system respects the `MAX_CONCURRENT_CHUNKS` limit to prevent memory exhaustion
- **THEN** the final dataframe merges all AI chunk results accurately
