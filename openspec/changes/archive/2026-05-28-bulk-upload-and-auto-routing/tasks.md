## 1. Database Schema & Migration

- [x] 1.1 Add `Batch` model to `backend/models.py` with fields: `id`, `user_id`, `status`, `created_at`.
- [x] 1.2 Add `batch_id` foreign key (nullable) to `ProcessingJob` model linking each job to a parent Batch.
- [x] 1.3 Add `hs_code_prefixes` text field (nullable) to the `Dictionary` model for storing comma-separated 4-digit HS prefixes.
- [x] 1.4 Write a one-time migration script to scan existing dictionary CSV files, extract unique 4-digit HS prefixes from the `Mã HS` column, and populate `hs_code_prefixes`.
- [x] 1.5 Update the Dictionary Generator wizard endpoint to auto-populate `hs_code_prefixes` when a new dictionary is generated/uploaded.

## 2. Backend: Batch Upload & Queue

- [x] 2.1 Refactor `/upload` endpoint in `backend/main.py` to accept `List[UploadFile]` and create a `Batch` + multiple `ProcessingJob` records.
- [x] 2.2 Implement sequential `BatchQueueManager` using `asyncio.Queue` to process jobs one-by-one within a batch.
- [x] 2.3 Add Import/Export auto-detection: scan for `VN_Importer`/`VN_Exporter` columns, add `Loại giao dịch` column to cleaned output.

## 3. Backend: BI-Ready Sanitization

- [x] 3.1 Refactor date handling in `data_cleaner.py`: keep full `Date` as ISO `YYYY-MM-DD` in `Ngày` column, add separate `Tháng` column (integer 1-12). Remove the `"Tháng X"` text conversion.
- [x] 3.2 Apply `pd.to_numeric(..., errors='coerce')` to `Lượng`, `Giá trị`, `Đơn giá` columns after stripping commas/currency text.
- [x] 3.3 Apply column header rename map: `Method_of_Payment` → `Phương thức thanh toán`, drop `.1` suffix duplicates.

## 4. Backend: Context-Aware Dictionary Routing

- [x] 4.1 Implement HS prefix scanner: extract unique 4-digit prefixes from `HS_Code` column of raw file.
- [x] 4.2 Implement dictionary routing query: find `Dictionary` records where `hs_code_prefixes` overlaps with detected prefixes, select highest overlap. Fall back to active dictionary.
- [x] 4.3 Pass the selected dictionary path to the cleaning pipeline instead of always using the globally active dictionary.

## 5. Backend: Batch Download Endpoints

- [x] 5.1 Add `/api/batches/{batch_id}/download-merged` endpoint: concatenate all cleaned files into a single Excel with `Tên file nguồn` and `Loại giao dịch` columns.
- [x] 5.2 Add `/api/batches/{batch_id}/download-zip` endpoint: bundle all cleaned files into a ZIP archive.
- [x] 5.3 Add `/api/batches/{batch_id}/insights` endpoint: return aggregate stats (product line counts, NC/LK ratio, top 5 companies).

## 6. Frontend: Batch Upload UI

- [x] 6.1 Update `CleanData.tsx` to support multi-file drag-and-drop selection (HTML5 `multiple` attribute).
- [x] 6.2 Add transaction type confirmation UI: show auto-detected type per file with manual override toggle before processing.
- [x] 6.3 Build batch queue status tracker showing file-level progress (`Pending` → `Processing 45%` → `Done`).

## 7. Frontend: Batch Preview & Charts

- [x] 7.1 Install `recharts` in `frontend/package.json`.
- [x] 7.2 Refactor Preview Dialog to display consolidated read-only grid with `Tên file nguồn` column and "Cần kiểm tra" filter toggle.
- [x] 7.3 Build Quick Market Insights panel: Doughnut chart (Product Lines), Pie chart (NC/LK ratio), Bar chart (Top 5 companies by value).
- [x] 7.4 Add download buttons: "Tải file gộp (Excel)", "Tải tất cả (ZIP)", and per-file download links.

## 8. Verification

- [x] 8.1 Test batch uploading 3 mixed Excel/CSV files and verify sequential processing.
- [x] 8.2 Verify auto-detected transaction type is correct and overridable.
- [x] 8.3 Verify dictionary auto-routing selects the correct dictionary based on HS code overlap.
- [x] 8.4 Verify cleaned output: `Ngày` is ISO `YYYY-MM-DD`, `Tháng` is integer, numeric columns are clean floats, headers are unified Vietnamese.
- [x] 8.5 Verify merged Excel and ZIP downloads contain correct data with source file and transaction type columns.
- [x] 8.6 Verify mini-charts render correct aggregate statistics in the batch preview.
