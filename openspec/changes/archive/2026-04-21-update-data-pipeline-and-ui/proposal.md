## Why

The current data processing pipeline needs to be converted from its Jupyter Notebook format (`PhoBertmappingv2(85%).ipynb`) into a production-ready Python backend. It must properly distinguish between import (NK) and export (XK) streams according to `dataset/xk_nk_diff.csv` to retain stream-specific unpredicted columns. Furthermore, the core product classification logic must implement a hybrid approach utilizing the `dataset/dictv3.csv` dictionary with high-weight words as the primary categorization tool, falling back to the AI model only when confidence is low. Finally, the frontend user experience is opaque during data processing without an ability to preview the final Excel output. This change solves these processing gaps and enhances user visibility.

## What Changes

- Port the raw data mapping, preprocessing, and hybrid classification logic from `PhoBertmappingv2(85%).ipynb` to the Python backend.
- Distinguish and process data streams differently based on export (XK) and import (NK) markers found in `dataset/xk_nk_diff.csv`.
- Append non-predictive columns directly into the cleaned data file based on the stream type.
- Implement the "Hybrid Classification" logic combining `dataset/dictv3.csv`, high-weight keywords, and PhoBERT fallback.
- Update the frontend to show real-time logs/progress of the data processing pipeline stages.
- Add an Excel preview feature on the frontend so users can see the final processed output before downloading.

## Capabilities

### New Capabilities
- `data-stream-separation`: Separation of import (NK) and export (XK) streams and handling of non-predictive columns.
- `dictionary-filtering`: Hybrid product categorization using `dataset/dictv3.csv` and high-weight words, falling back to AI.
- `pipeline-monitoring-ui`: Real-time frontend logging for tracking data processing stages.
- `excel-preview-ui`: Frontend preview of the final Excel output.

### Modified Capabilities

## Impact

- **Backend**: Updates `main.py` and `core/data_cleaner.py` (or similar scripts) to run the full notebook pipeline: mapping, dictionary logic, text masking, high-weight scoring, and real-time progress updates (e.g., via SSE).
- **Frontend**: Updates `app.js`, `index.html`, and `style.css` to consume progress updates and render the Excel preview.
- **Dependencies**: The backend will require `transformers`, `torch`, `pandas` etc., as used in the original notebook.
