## 1. Setup Keyword Filtering Lists

- [x] 1.1 In `backend/core/dict_generator.py`, define a `GLOBAL_STOPWORDS` set inside the `DictionaryGenerator` class (or at the top level) containing generic brands and terms: `{'hiệu', 'công suất', 'kích thước', 'jindian', 'philips', 'gp', 'rạng đông', 'điện quang', 'panasonic', 'samsung', 'lg', 'toshiba', 'màu sắc', 'bảo hành'}`.
- [x] 1.2 In `backend/core/dict_generator.py`, define a `CONTEXT_RESTRICTED` dict containing mapping of keywords to required category contexts: `{'mặt trời': ['năng lượng mặt trời', 'solar'], 'solar': ['năng lượng mặt trời', 'solar'], 'nlmt': ['năng lượng mặt trời', 'solar']}`.

## 2. Update Keyword Extraction Logic

- [x] 2.1 In `backend/core/dict_generator.py`, locate the `extract_keywords_ai` function.
- [x] 2.2 Add a check at the beginning of candidate evaluation (`for n, lf in class_f[i].items():`). Split the n-gram `n` into words. If ANY word is in `GLOBAL_STOPWORDS`, `continue` (skip this candidate).
- [x] 2.3 Add the context check: If any word in the n-gram exists as a key in `CONTEXT_RESTRICTED`, retrieve the required contexts. Check if ANY of the required contexts exist in `fb[i]` (Lớp 1 or Lớp 2) or `loai`. If not, `continue` (skip this candidate).

## 3. Generate New Dictionary and Verify

- [x] 3.1 Run the dictionary generator script (or trigger it via the backend API / `generate_dict` endpoint) to regenerate `TONG_THE.csv`.
- [x] 3.2 Inspect `TONG_THE.csv` (or the `deep_analysis` output) to confirm that the row for "đèn côn trùng" no longer contains the keyword "mặt trời hiệu" or "mặt trời hiệu jindian".
- [x] 3.3 Confirm that "đèn năng lượng mặt trời" still retains its "mặt trời" related keywords correctly.
