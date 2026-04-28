## 1. Analysis and Setup

- [x] 1.1 Read the reference header order from `sample.csv` or define it as a static list in the code.
- [x] 1.2 Identify where the final output CSV/Excel file is generated (likely `backend/core/data_cleaner.py` or `extracted_pipeline.py`).

## 2. Implementation

- [x] 2.1 Update the data export logic to reorder columns matching `sample.csv` (using `df.reindex(columns=...)` or similar safe method).
- [x] 2.2 Add logic to explicitly separate the "Trạng thái" and "Độ tự tin" columns from the DataFrame if present.
- [x] 2.3 Append "Trạng thái" and "Độ tự tin" as the very last two columns of the final DataFrame before exporting.

## 3. Testing and Validation

- [x] 3.1 Run the pipeline to generate a test output file.
- [x] 3.2 Verify the final output file headers match the expected order and that "Trạng thái" and "Độ tự tin" are at the end.