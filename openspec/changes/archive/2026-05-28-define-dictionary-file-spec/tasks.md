## 1. Documentation and Specification

- [x] 1.1 Create `DICTIONARY_SPEC.md` in the project root based on the design and specs
- [x] 1.2 Document mandatory columns: `Keyword`, `Dòng SP`, `Loại`, `Lớp 1`, `Lớp 2`, `Mã HS`
- [x] 1.3 Document normalization rules for keywords (lowercase, special characters)
- [x] 1.4 Document scoring rules (High Value, Junk, Regular)

## 2. Dictionary Audit and Update

- [x] 2.1 Inspect `dataset/dictv2.csv` and `dataset/dictv3.csv` for adherence to the new spec
- [x] 2.2 Standardize all "unknown" values to "không_có"
- [x] 2.3 Clean up keywords (remove duplicates, normalize strings)
- [x] 2.4 Verify that all rows have the required columns

## 3. Backend Verification (Optional/Refinement)

- [x] 3.1 Review `_load_dict` in `backend/core/dictionary_matcher.py` to ensure it handles the mandatory columns correctly
- [x] 3.2 Add a simple validation check/warning if a dictionary file is missing columns or using incorrect encoding
