## ADDED Requirements

### Requirement: Offline Custom Dataset Pre-loading
The system SHALL load the offline customs dataset from the `HSCustomsReference` database table into an in-memory cache upon server startup.

#### Scenario: Server Startup
- **WHEN** the FastAPI server initializes
- **THEN** it pre-loads the full HS Customs Reference dataset into memory for rapid access.

### Requirement: O(1) HS Code Resolution
The data cleaning pipeline SHALL resolve HS codes by querying the in-memory cache instead of relying on external web crawling.

#### Scenario: Normal Lookup
- **WHEN** an uploaded dataset contains an HS Code
- **THEN** the system resolves the Dòng SP, Lớp 1, and Lớp 2 using the in-memory cache, responding in under 10ms.

#### Scenario: Fallback Lookup
- **WHEN** an HS Code is not found in the in-memory cache or requires further analysis
- **THEN** the system invokes the DeepSeek API fallback mechanism.
