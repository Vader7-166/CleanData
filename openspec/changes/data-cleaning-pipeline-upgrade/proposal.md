## Why

The current data cleaning pipeline is slow, memory-intensive, and relies on online web crawling (via `httpx` to various websites) to resolve HS codes, which introduces latency, unreliability, and potential extra costs. Furthermore, when users upload multiple raw data files, the system processes them individually and reads them entirely into memory (`pd.concat` or individual DataFrames), risking Out-Of-Memory (OOM) errors and missing out on the efficiency of batch multiprocessing. This change is needed to build a highly scalable, offline-first HS Code taxonomy and implement a memory-safe streaming file merge pipeline.

## What Changes

- **Offline HS Code Taxonomy (In-Memory Cache):** Introduce a new database model `HSCustomsReference` to store ~11,000 customs rows offline. Upon startup, this data is cached in memory (Radix Tree/Dict) to guarantee <1ms lookup speeds without continuous DB queries.
- **OpenAI Client for DeepSeek API:** Migrate the current raw `httpx` HTTP calls for DeepSeek fallback logic to the official `openai` Python client for better connection pooling, retries, and stability.
- **Memory-Safe Streaming File Merge:** Refactor the bulk upload API to read uploaded chunks and append them sequentially to a temporary Master CSV file on disk (`merged_job.csv`). This prevents pandas from consuming excess RAM during concatenation.
- **Admin-Priority Dictionary Merging:** Implement logic to build a unified Aho-Corasick automaton from multiple active dictionaries. When conflicts arise, dictionary terms created by Admins overwrite user-defined terms.
- **Global Process Pool:** **BREAKING** Refactor the asynchronous data cleaning pipeline to use a centralized, global `ProcessPoolExecutor` initialized at startup. This prevents the severe "fork bomb" bug where every user request spins up new concurrent multi-processing environments, leading to Out-Of-Memory (OOM) crashes.
- **UI Performance & Chart Fixes:** Refactor the Batch Preview frontend to use `Promise.all` for parallel fetching (or a unified API), add custom tooltips and truncation to Recharts to prevent overflow/clipping of long product names, and fix the React table keying anti-pattern.

## Capabilities

### New Capabilities
- `offline-hs-taxonomy`: Building and caching an offline customs dataset for rapid in-memory taxonomy lookup.
- `streaming-batch-merge`: A memory-safe algorithm to stream multiple uploaded files into a single master temporary CSV on disk before applying data cleaning.
- `admin-priority-aho-corasick`: Mechanism to generate a multi-dictionary Aho-Corasick automaton with Admin conflict-resolution priority.
- `deepseek-openai-client`: Refactored LLM fallback module utilizing the OpenAI client for DeepSeek.
- `global-process-pool`: A globally initialized process pool executor for safely handling CPU-bound NLP tasks in a web server environment.
- `ui-performance-fixes`: Frontend UI polish including parallel API fetching, robust chart rendering (truncation, margins), and robust table construction.

### Modified Capabilities


## Impact

- **Database:** `models.py` (New `HSCustomsReference` model, potentially adding `role` or `priority` checks for `Dictionary`).
- **Scripts:** `scripts/import_hs_dataset.py` (New script to ETL Excel customs data into DB).
- **Backend API:** `main.py` (`/upload` and `/api/dictionaries/upload` endpoints need to handle streaming/appending).
- **Core Processing:** `core/dict_generator.py`, `core/data_cleaner.py`, `core/crawler.py` (Migrating to OpenAI client, adapting multi-dictionary merging logic, and extracting the ProcessPoolExecutor to global scope).
- **Frontend UI:** `frontend/src/components/BatchPreviewDialog.tsx` (Refactoring API calls, Recharts layout, and Table render logic).
