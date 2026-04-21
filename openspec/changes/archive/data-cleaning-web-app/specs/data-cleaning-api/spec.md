## ADDED Requirements

### Requirement: REST API for Processing
The backend SHALL expose a POST endpoint to upload a dataset, run it through the loaded TF-IDF dictionary and NLP model, and return the cleaned output.

#### Scenario: User uploads CSV for cleaning
- **WHEN** client sends a mapped multipart payload with a valid data file
- **THEN** the API processes using the model in `/working` and returns a download link or stream of the cleaned file
