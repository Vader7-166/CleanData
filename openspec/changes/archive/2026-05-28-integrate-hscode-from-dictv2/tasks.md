## 1. Backend Core Updates

- [x] 1.1 Update `DataCleaner._load_dict` in `backend/core/data_cleaner.py` to extract the `Mã HS` (HS CODE) column from dictionary rows, defaulting to `'không_có'` if missing.
- [x] 1.2 Modify `DataCleaner.predict_dictionary` in `backend/core/data_cleaner.py` to append the matched `Mã HS` to the `label_str` result (5 segments total).
- [x] 1.3 Update the `split_and_assign` helper function within `DataCleaner.process_async` to split the result into 5 segments and assign the 5th segment to the `Mã HS` column.
- [x] 1.4 Update the default dictionary path to `dataset/dictv2.csv` in both the `DataCleaner.__init__` method and the `get_cleaner` factory function in `backend/core/data_cleaner.py`.

## 2. Validation and Testing

- [x] 2.1 Verify that the `DataCleaner` correctly loads `dataset/dictv2.csv` and handles the new column without errors.
- [x] 2.2 Perform a test cleaning job using a sample dataset that triggers dictionary matches, and verify that the output Excel file contains the corrected `Mã HS` values from the dictionary.
