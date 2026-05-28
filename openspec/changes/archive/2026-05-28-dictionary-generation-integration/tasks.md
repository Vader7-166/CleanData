## 1. Backend: Core Logic & Dependencies

- [x] 1.1 Add `scikit-learn`, `pyvi`, `groq`, `openpyxl`, and `python-dotenv` to `backend/requirements.txt`.
- [x] 1.2 Initialize `python-dotenv` in `backend/main.py` or a shared config to load `GROQ_API_KEY`.
- [x] 1.3 Port and refactor clustering logic to `backend/core/dict_generator.py`.
- [x] 1.4 Port and refactor LLM labeling logic into the `DictionaryGenerator` class.
- [x] 1.5 Port and refactor keyword extraction logic into the `DictionaryGenerator` class.

## 2. Backend: API Implementation

- [x] 2.1 Implement `/api/dictionaries/generate/step1` (Raw Upload -> Draft Excel).
- [x] 2.2 Implement `/api/dictionaries/generate/step2` (Draft + Raw Upload -> Final Dictionary).
- [x] 2.3 Ensure temporary file cleanup for uploaded raw/draft files.

## 3. Frontend: Generator Wizard UI

- [x] 3.1 Create `DictionaryGeneratorWizard` component.
- [x] 3.2 Implement Step 1 UI flow (Upload raw, select Dòng SP, handle processing state).
- [x] 3.3 Implement Step 2 UI flow (Upload reviewed draft, finalize, and refresh dictionary list).
- [x] 3.4 Integrate the wizard entry point into `Dictionary.jsx`.

## 4. Verification

- [x] 4.1 Verify end-to-end flow with sample data from `Create_Dictionary/Raw`.
- [x] 4.2 Validate final dictionary CSV against `DICTIONARY_SPEC.md`.
