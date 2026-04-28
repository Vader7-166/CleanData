## MODIFIED Requirements

### Requirement: Dictionary File Upload
The system SHALL provide an endpoint to upload CSV files to be used as dictionaries for product classification AND SHALL associate the upload with the currently authenticated user.

#### Scenario: Successful CSV Upload with User Link
- **WHEN** an authenticated user uploads a valid CSV file
- **THEN** the system SHALL store the file AND record its metadata in the database including a reference to the `user_id` of the uploader.
