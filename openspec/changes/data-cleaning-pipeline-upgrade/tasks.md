## 1. Database & Offline Dataset

- [x] 1.1 Create `HSCustomsReference` model in `backend/models.py`.
- [x] 1.2 Create `backend/scripts/import_hs_dataset.py` to read `dataset/vn_customs_hs_codes.xlsx` and populate `HSCustomsReference`.
- [x] 1.3 Add application startup event in `backend/main.py` to load the `HSCustomsReference` table into an in-memory dictionary.

## 2. OpenAI Client Integration

- [x] 2.1 Add `openai` library to `backend/requirements.txt`.
- [x] 2.2 Refactor `backend/core/crawler.py` to use `openai.AsyncOpenAI` for the DeepSeek fallback query instead of `httpx`.
- [x] 2.3 Refactor `backend/core/dict_generator.py` to use `openai.AsyncOpenAI` if applicable.

## 3. Data Cleaning Core Engine Updates

- [x] 3.1 Update `backend/core/data_cleaner.py` to bypass online web crawling entirely if the HS Code is successfully resolved by the in-memory `HSCustomsReference` cache.
- [x] 3.2 Update dictionary loading logic in `backend/core/data_cleaner.py` to fetch all active dictionaries, sort them (Admin vs User priority), and construct a unified Aho-Corasick automaton.
- [x] 3.3 Refactor `backend/core/data_cleaner.py` to initialize the `ProcessPoolExecutor` globally instead of inside `process_async`.

## 4. Bulk Upload Streaming Architecture

- [x] 4.1 Update `@app.post("/upload")` in `backend/main.py` to merge all uploaded files into a single temporary `merged_job_<id>.csv` on disk incrementally (using stream/chunk logic).
- [x] 4.2 Update `backend/main.py` queue logic to run `process_async` exactly once per batch on the unified master file.
- [x] 4.3 Clean up redundant individual file processing loops in `process_batch` and `process_job`.

## 5. UI Performance & Rendering Fixes

- [x] 5.1 Refactor `frontend/src/components/BatchPreviewDialog.tsx` to fetch preview data using `Promise.all` for parallel execution.
- [x] 5.2 Update `PieChart` and `BarChart` in `BatchPreviewDialog.tsx` with custom tooltips, label truncation, and proper margins to prevent clipping.
- [x] 5.3 Fix React anti-patterns in the Table by extracting all unique column keys across the entire `filteredData` set and using unique row keys.
