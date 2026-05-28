## Why

Currently, creating data dictionaries is a manual and labor-intensive process for users. Integrating the automated dictionary generation pipeline (clustering + LLM labeling) will significantly speed up the workflow, reduce human error, and allow users to generate high-quality taxonomies and keywords directly from raw data within the application.

## What Changes

- **Automated Taxonomy Generation**: New backend service to cluster raw product data using TF-IDF and DBSCAN.
- **LLM-Powered Labeling**: Integration with Groq (Llama 3) to automatically assign human-readable names to product clusters.
- **Keyword Extraction Pipeline**: Automated extraction of the most frequent keywords for each product category.
- **Two-Step Wizard UI**: A new interface in the Dictionary page to guide users through the generation, review, and finalization process.
- **Dictionary Management Updates**: New endpoints to handle intermediate draft files and final dictionary persistence.

## Capabilities

### New Capabilities
- `dictionary-generation-wizard`: A multi-step UI flow for creating dictionaries from raw data.
- `llm-cluster-labeling`: Backend capability to use LLMs for naming discovered product clusters.
- `automated-keyword-extraction`: Backend logic to extract keywords from raw data based on a taxonomy.

### Modified Capabilities
- `dictionary-management-page`: Enhance the dictionary page to include generation features.

## Impact

- **Backend**: New `backend/core/dict_generator.py` module; updated `backend/main.py` with new endpoints; `backend/requirements.txt` updated with `scikit-learn`, `pyvi`, `groq`, and `openpyxl`.
- **Frontend**: Significant updates to `Dictionary.jsx` and new components for the generation wizard.
- **Environment**: Requirement for `GROQ_API_KEY` in the backend environment.
