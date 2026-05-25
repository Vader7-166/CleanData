## Context

Users processing multiple batches of data find it inefficient to upload and pair each file with a dictionary manually. Standardized naming conventions are often used by users, which can be leveraged to automate this pairing process.

## Goals / Non-Goals

**Goals:**
- Allow multiple files to be uploaded in a single action.
- Automatically suggest the best dictionary for each uploaded file based on its filename.
- Provide a clear UI for reviewing and confirming auto-mappings.

**Non-Goals:**
- Automatic execution of processing without user confirmation (users must still click "Process").
- Handling complex file formats beyond Excel/CSV.

## Decisions

- **Decision 1: Regex-based Pattern Matching**: Use regular expressions to extract key identifiers (HS Code, Year, Region) from filenames.
  - Pattern example: `(\d{4})[-_].*(\d{4})` to capture a 4-digit code and a 4-digit year.
- **Decision 2: Dictionary Lookup Service**: Create a backend service that scans the `storage/dictionaries` directory and builds an index of available dictionaries for quick matching.
- **Decision 3: Multi-part File Upload**: Use standard multipart/form-data for bulk uploads, ensuring the backend handles file streaming to avoid memory exhaustion.
- **Decision 4: Mapping Metadata**: The backend will return a list of `(file_id, suggested_dict_id, confidence_score)` to the frontend.

## Risks / Trade-offs

- [Risk] → Ambiguous filenames might lead to incorrect auto-routing.
- [Mitigation] → Always allow users to manually change the dictionary selection before starting the process.
- [Risk] → Large bulk uploads might timeout the HTTP request.
- [Mitigation] → Implement asynchronous upload processing or increase timeout limits for the upload endpoint.
