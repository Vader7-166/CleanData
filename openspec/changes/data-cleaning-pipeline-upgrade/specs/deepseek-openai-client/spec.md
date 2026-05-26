## ADDED Requirements

### Requirement: OpenAI Client Integration for DeepSeek
The system SHALL use the official Python `openai` client package to interact with the DeepSeek API, replacing raw HTTP requests.

#### Scenario: Fallback API Call
- **WHEN** the system needs to query the DeepSeek API for HS code classification or text generation
- **THEN** it utilizes the `openai.AsyncOpenAI` client configured with the DeepSeek API base URL and API key to manage connection pooling and retries efficiently.
