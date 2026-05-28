## Context

The system processes large batches of customs data, resolving text descriptions to standardized HS Codes and Product Lines. Currently, HS Code resolution involves querying external websites (hscode.pro.vn, customs.gov.vn) and appending fallback LLM queries. Bulk file uploads are processed as independent parallel jobs, which risks running out of RAM if all files are loaded into memory concurrently or if files are merged using `pd.concat()`.

## Goals / Non-Goals

**Goals:**
- Guarantee <10ms lookup speeds for known HS Codes using an offline dataset.
- Process arbitrarily large batches of input files without causing memory exhaustion.
- Provide a clear conflict resolution strategy when multiple active dictionaries have overlapping keywords.
- Improve the reliability of the DeepSeek LLM fallback by using the official SDK.

**Non-Goals:**
- Completely rewriting the core NLP data cleaning logic (`process_async`).
- Changing the structure of the final exported Excel/CSV outputs.

## Decisions

**1. In-Memory Cache for HS Codes**
- **Decision:** Load the entire `HSCustomsReference` table (~11,000 rows) into a Python dictionary upon server startup.
- **Rationale:** 11k rows consume less than 5MB of RAM. An in-memory dictionary provides O(1) lookup time, eliminating the overhead of SQLAlchemy/Database queries for each row processed in the dataset, easily meeting the <10ms requirement.

**2. Chunked Appending for Master File Generation**
- **Decision:** Instead of using `pd.concat()` in memory, the system will read each uploaded file in streams (or using pandas `chunksize`) and append the data sequentially to a single `merged_job_<id>.csv` on disk.
- **Rationale:** This ensures the RAM footprint remains stable and small (only the size of the current chunk) regardless of whether the user uploads one 50MB file or ten 50MB files. The downstream cleaning pipeline can then read this single master file efficiently.

**3. Admin-Priority Automaton Building**
- **Decision:** When building the `ahocorasick.Automaton` from multiple active dictionaries, dictionaries will be sorted by their priority (Admin-owned first, or simply applying Admin dictionaries last to overwrite previous entries).
- **Rationale:** The Aho-Corasick library allows updating keys. By inserting the User dictionary keys first, and then the Admin dictionary keys second, the Admin's keys will overwrite the User's if there is a conflict.

**4. Official OpenAI Client for DeepSeek**
- **Decision:** Replace `httpx` HTTP calls with the `openai.AsyncOpenAI` client pointing to `https://api.deepseek.com`.
- **Rationale:** Provides built-in connection pooling, exponential backoff/retries, and type hints, reducing boilerplate networking code.

**5. Global Process Pool for NLP Cleaning**
- **Decision:** Extract the `ProcessPoolExecutor` from within the request-scoped `process_async` function and initialize it globally when the FastAPI app starts.
- **Rationale:** Creating a new ProcessPool per request can exponentially multiply the number of processes (Request Count * CPU Cores), causing a massive memory leak and "fork bomb" effect. A global pool restricts the maximum concurrent NLP cleaning processes to exactly the number of CPU cores, ensuring stable performance under heavy load.

**6. Frontend Batch Preview Resilience**
- **Decision:** Refactor `BatchPreviewDialog.tsx` to execute API requests concurrently with `Promise.all`, dynamically extract all table columns across the dataset, and properly truncate Recharts labels.
- **Rationale:** Sequential loops over 50+ files cause severe UI freezing and network waterfalling. Dynamic column extraction prevents missing data when the first row has nulls. Properly configured Recharts margins and custom tooltips prevent UI clipping for lengthy text.

## Risks / Trade-offs

- **Risk: Startup Delay** → Loading 11k rows from SQLite to memory and building the Aho-Corasick Trie might add 1-2 seconds to the API startup time.
  - *Mitigation:* This is a one-time penalty at boot and acceptable for a backend service.
- **Risk: Schema Variations in Merged Files** → If uploaded files have different columns, appending them to a CSV could cause misaligned headers.
  - *Mitigation:* The backend will perform a schema check on the first chunk of each file to ensure the core columns (e.g., `Mã HS`, `Tên hàng`) exist before merging.
