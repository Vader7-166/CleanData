## Context

The current data processing pipeline is currently drafted in `PhoBertmappingv2(85%).ipynb` and needs to be ported into the backend (`core/data_cleaner.py`). It needs to handle import (NK) and export (XK) streams differently due to varying columns defined in `dataset/xk_nk_diff.csv`. The output needs to be a unified, cleaned dataset retaining non-predictive columns from the original input based on stream type. Furthermore, the core product prediction is a "Hybrid" model: a dictionary-based categorizer (`dataset/dictv3.csv` with high-weight words) is run first, and a PhoBERT AI model is used as a fallback. Finally, the UI is completely decoupled from backend processing progress, and users have no visibility into intermediate stages or final output preview before downloading.

## Goals / Non-Goals

**Goals:**
- Convert the Jupyter notebook's Python code into `core/data_cleaner.py` and integrate it with the FastAPI backend.
- Separate processing logic for NK (import) vs. XK (export) streams to keep their distinct unpredicted columns from `xk_nk_diff.csv`.
- Implement the dictionary-based hybrid mapping exactly as the notebook (`dictv3.csv`, `HIGH_VALUE_KEYWORDS`, `JUNK_KEYWORDS`, masking text algorithm).
- Introduce real-time processing logs via SSE to the frontend.
- Provide an Excel preview UI using a lightweight frontend library.

**Non-Goals:**
- Retraining the PhoBERT model. We will load existing checkpoints.
- Creating a full-fledged data visualization dashboard; we only need an Excel preview.

## Decisions

- **Pipeline Conversion:** We will map the two main phases of the notebook (Raw mapping and Hybrid Prediction) into modular functions inside the backend so they can be executed sequentially or asynchronously while emitting progress events.
- **Stream Routing Strategy:** The backend will first inspect the uploaded data's columns to determine if it is NK or XK based on `dataset/xk_nk_diff.csv`. It will extract the unique columns, pass the text fields to the Hybrid Predictor, and append the unique columns back.
- **Hybrid Classification Mechanism:** The `dict_mapping` dictionary will be pre-loaded in memory using `dataset/dictv3.csv`. Text masking and high-weight word scoring will be executed before any tensors are passed to PhoBERT.
- **Real-time Logging:** We will use SSE (Server-Sent Events) from FastAPI (`main.py`) because it is unidirectional (server-to-client) and simpler to implement than WebSockets for just streaming logs.
- **Excel Preview:** The backend will generate the final DataFrame and serialize a subset (first 100 rows) to JSON, returning it to the frontend via a preview endpoint.

## Risks / Trade-offs

- **Memory Usage:** Loading `dictv3.csv` and a PhoBERT model into RAM could consume substantial memory. Mitigation: `dictv3` is relatively small, but PhoBERT requires a machine with enough memory. We will ensure models are loaded correctly with PyTorch.
- **Processing Time:** The pipeline can take time for large Excel files. Mitigation: Using SSE keeps the connection alive and the user informed, avoiding timeouts.
