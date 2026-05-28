## Context

The current pipeline processes one file at a time using a single globally-active dictionary. The output files have formatting issues that prevent direct import into PowerBI:
- The `Ngày` column is converted to text like `"Tháng 12"` (losing the original date and making time-series sorting impossible).
- Numeric columns (`Lượng`, `Giá trị`, `Đơn giá`) are stored as raw strings from the source (may contain commas, currency symbols).
- Column names mix English (`Method_of_Payment`) and Vietnamese, and pandas generates duplicate suffixes like `Công suất.1`.
- CSV export already uses `utf-8-sig` (no action needed here).
- Dictionary files are not tagged with HS codes, so there is no way to auto-match a dictionary to a file.

## Goals / Non-Goals

**Goals:**
- Allow multiple files to be uploaded and processed in a single batch.
- Auto-detect Import/Export transaction type per file.
- Auto-select the best dictionary for each file based on HS codes in the data.
- Sanitize dates (ISO format), numbers (clean floats), and column headers (unified Vietnamese).
- Provide a batch-level read-only preview dashboard with quick insight charts.
- Support flexible download: individual files, merged Excel, or ZIP.

**Non-Goals:**
- Inline editing or bulk-approving individual rows on the web UI (too complex; users will correct data in Excel/PowerBI after download).
- Parallel processing of multiple files simultaneously (sequential queue to protect server resources).
- Automatic dictionary generation (dictionaries must be generated separately via the wizard first).

## Decisions

### Decision 1: Sequential Batch Queue
- **Approach**: Introduce a `Batch` model in the database. Uploading multiple files creates one `Batch` containing multiple `ProcessingJob` records. A background worker processes them one by one using `asyncio.Queue`.
- **Why not parallel**: The AI model and dictionary matcher are CPU-intensive. Running multiple files concurrently on a single-core Docker container would cause OOM or severe slowdowns.

### Decision 2: Dictionary ↔ HS Code Linkage
- **Problem**: The `Dictionary` model currently has no field linking it to specific HS codes. Dictionary CSV files already contain a `Mã HS` column per keyword row, but there is no database-level metadata.
- **Solution**: Add a `hs_code_prefixes` text field to the `Dictionary` model (comma-separated 4-digit prefixes, e.g. `"8539,9405,7020"`). This field is auto-populated when a dictionary is generated via the wizard by scanning the `Mã HS` column of the output CSV. For existing dictionaries, provide a one-time migration that scans each dictionary file and extracts unique 4-digit prefixes.
- **Routing logic**: When processing a raw file, extract the unique 4-digit HS prefixes from the `HS_Code` column. Query `Dictionary` records where `hs_code_prefixes` overlaps with the detected set. Select the dictionary with the highest overlap count. Fall back to the globally active dictionary if no match is found.

### Decision 3: BI-Ready Sanitization Pipeline
- **Dates**: Keep the full original `Date` column parsed as `YYYY-MM-DD` (or empty if unparseable). Add a separate `Tháng` column (integer 1-12) for pivot analysis. Remove the current `"Tháng X"` text conversion.
- **Numeric Fields**: Apply `pd.to_numeric(..., errors='coerce')` to `Quantity`, `Total_Value_USD`, `Unit_Price_USD` after stripping commas, dollar signs, and currency text.
- **Column Header Unification**: Apply a hardcoded rename map: `Method_of_Payment` → `Phương thức thanh toán`, `Incoterms` stays as-is (international standard). Drop columns ending in `.1` suffix (pandas duplicates).

### Decision 4: Read-Only Consolidated Preview with Charts
- **Backend**: Add `/api/batches/{batch_id}/insights` returning aggregate stats.
- **Frontend**: Use `recharts` library (lightweight, React-native) for: Doughnut chart (Product Lines), Pie chart (NC/LK ratio), Bar chart (Top 5 companies by value).
- **Why read-only**: Building an inline editor that modifies Excel files on the server is fragile and unnecessary. Users download files and use Excel/PowerBI for corrections.

### Decision 5: Flexible Download Options
- Individual file download (existing `/api/jobs/{job_id}/download`).
- Merged Excel download: new endpoint `/api/batches/{batch_id}/download-merged` that concatenates all cleaned files with `Tên file nguồn` and `Loại giao dịch` columns.
- ZIP download: new endpoint `/api/batches/{batch_id}/download-zip` that bundles all individual cleaned files.

## Risks / Trade-offs

- [Risk] → A raw file may contain HS codes from multiple industries, making dictionary selection ambiguous.
- [Mitigation] → Select the dictionary with highest prefix overlap. If no clear winner, use the active dictionary and log a warning.
- [Risk] → Adding `hs_code_prefixes` to existing dictionaries requires a one-time migration scan.
- [Mitigation] → Write a migration script that reads each dictionary CSV and extracts unique 4-digit HS prefixes to populate the field.
- [Risk] → Large bulk uploads (10+ files) may timeout the HTTP request.
- [Mitigation] → Upload endpoint returns immediately with `batch_id`; all processing is async in background.
- [Risk] → Some raw files from different data providers may not have a `Date` column or may use non-standard date formats.
- [Mitigation] → Gracefully default to empty `Ngày` and `Tháng` columns when parsing fails.
