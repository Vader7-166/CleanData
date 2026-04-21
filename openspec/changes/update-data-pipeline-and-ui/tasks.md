## 1. Setup & Preparation

- [ ] 1.1 Analyze `dataset/xk_nk_diff.csv` and configure the column sets that distinguish XK (export) from NK (import) streams.
- [ ] 1.2 Verify `dataset/dictv3.csv` and integrate its loading logic into `core/data_cleaner.py`.
- [ ] 1.3 Add necessary ML dependencies (`torch`, `transformers`, `scikit-learn`) to `backend/requirements.txt` based on `PhoBertmappingv2(85%).ipynb`.

## 2. Backend: Data Pipeline Porting & Routing

- [ ] 2.1 Port the raw data mapping logic from the notebook into `core/data_cleaner.py` (mapping `Mã HS`, `Dòng SP`, etc.).
- [ ] 2.2 Update the mapping logic to detect if incoming data is XK or NK and preserve non-predictive columns specific to the detected stream.
- [ ] 2.3 Port the `trich_xuat_thong_tin` and `clean_text` functions from the notebook.
- [ ] 2.4 Port the `predict_hybrid` function, implementing the dictionary scoring loop (using `dictv3.csv`, `HIGH_VALUE_KEYWORDS`, `JUNK_KEYWORDS`, and text masking) and the `predict_with_threshold` PhoBERT fallback.

## 3. Backend: Real-time Logging & Preview APIs

- [ ] 3.1 Create an SSE endpoint in `main.py` for streaming real-time log messages.
- [ ] 3.2 Instrument data processing functions to yield/emit progress updates at major stages (Loading Data, Mapping, Hybrid Predicting, Finalizing).
- [ ] 3.3 Create a new endpoint (e.g., `/api/preview`) in `main.py` that returns the first 100 rows of the processed data as JSON.

## 4. Frontend: UI Implementation

- [ ] 4.1 Update `index.html` and `style.css` to include a progress log console and a preview table area.
- [ ] 4.2 Update `app.js` to connect to the backend logging stream and render live updates while processing.
- [ ] 4.3 Update `app.js` to fetch from the `/api/preview` endpoint and populate the UI preview table once processing completes.

## 5. Testing & Validation

- [ ] 5.1 Validate that the Python pipeline reproduces the exact categorization logic of the notebook using dictionary matching + AI fallback.
- [ ] 5.2 End-to-end test with a sample NK dataset, verifying the correct columns are retained, and the logs and preview render correctly.
- [ ] 5.3 End-to-end test with a sample XK dataset to ensure the pipeline routes and handles XK-specific columns correctly.
