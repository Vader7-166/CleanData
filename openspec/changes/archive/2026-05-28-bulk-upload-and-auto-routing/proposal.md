## Why

Market researchers must upload and configure data files one by one, and the resulting cleaned files contain formatting irregularities (non-standard date text "Tháng X" instead of full dates, text in numeric columns, and inconsistent column headers mixing English and Vietnamese) that require extensive manual post-cleaning in Power Query before they can be visualized in PowerBI or Excel. This proposal introduces bulk raw file upload, context-aware dictionary auto-routing, BI-ready data sanitization, and a consolidated batch preview dashboard to streamline the analytics workflow.

## What Changes

- **Bulk Upload & Sequential Processing Queue**: Enable uploading multiple raw files simultaneously and processing them sequentially via a backend task queue to prevent CPU overload.
- **Context-Aware Dictionary Auto-Routing**: Automatically pair each file with the best dictionary by scanning HS Codes inside the raw data and matching against a new `hs_code_prefixes` field on Dictionary records, eliminating manual active-dictionary switching.
- **Import/Export Transaction Auto-Detection**: Detect transaction type (`Nhập khẩu` or `Xuất khẩu`) based on presence of `VN_Importer`/`VN_Exporter` columns, adding a `Loại giao dịch` column with frontend manual override.
- **BI-Ready Data Sanitization**:
  - Preserve full date as ISO `YYYY-MM-DD` in a `Ngày` column, and add a separate `Tháng` column (integer 1-12) for pivot analysis.
  - Sanitize numeric columns (`Lượng`, `Giá trị`, `Đơn giá`) into clean float numbers (stripping commas, currency text).
  - Normalize column headers: rename `Method_of_Payment` → `Phương thức thanh toán`, remove pandas `.1` suffixes, and unify language.
- **Consolidated Batch Preview Dashboard**: A read-only batch preview page that aggregates data across files, filters rows needing review, and shows quick insight charts.
- **Flexible Download Options**: Support downloading individual cleaned files, a merged Excel file (all files combined with source/transaction-type columns), or a ZIP archive.

## Capabilities

### New Capabilities
- `bi-ready-batch-processing`: End-to-end pipeline for batch file uploads, sequential queue orchestration, BI-ready sanitization (dates, numbers, headers), and flexible download options.
- `context-aware-dictionary-routing`: Dynamic dictionary selection by matching HS codes in raw files against the `hs_code_prefixes` metadata stored on each Dictionary record.
- `batch-insights-dashboard`: A read-only unified batch preview UI with consolidated filtering, quick insight mini-charts (product line share, NC/LK ratio, top companies).

### Modified Capabilities
<!-- None -->

## Impact

- **Backend**:
  - `backend/models.py`: Add `Batch` model, add `hs_code_prefixes` and `batch_id` to `ProcessingJob` and `Dictionary`.
  - `backend/main.py`: Update upload/download APIs for batches, add batch insights endpoint.
  - `backend/core/data_cleaner.py`: Implement date/numeric/header sanitization and transaction-type tagging.
  - `backend/core/worker.py`: Accept dynamic dictionary path per file.
- **Frontend**:
  - `frontend/src/pages/CleanData.tsx`: Multi-file upload, transaction-type confirmation, queue tracking.
  - `frontend/src/pages/Dashboard.tsx`: Batch-level preview with consolidated filters and mini-charts.
  - `frontend/package.json`: Add `recharts` charting library.
