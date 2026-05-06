## ADDED Requirements

### Requirement: Multi-core Process Orchestration
The system SHALL employ a `ProcessPoolExecutor` to parallelize CPU-bound data cleaning tasks, bypassing the Python Global Interpreter Lock (GIL).

#### Scenario: Parallel Pass 1 execution
- **WHEN** a large dataset is processed
- **THEN** the system splits the `input_for_ai` data into chunks
- **THEN** these chunks are dispatched to multiple worker processes
- **THEN** dictionary matching and information extraction execute concurrently across all available CPU cores.

### Requirement: Persistent Worker Initialization
The system SHALL initialize worker processes with shared state (e.g., the Dictionary Matcher) once per worker lifetime to minimize per-chunk overhead.

#### Scenario: Efficient worker startup
- **WHEN** the `ProcessPoolExecutor` is started
- **THEN** an initializer function builds the Aho-Corasick automaton and loads dictionary metadata into the worker's memory
- **THEN** subsequent data chunks are processed without re-initializing the matcher.
