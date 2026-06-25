## 1. Setup and Environment Integration

- [x] 1.1 Create the analysis script `analysis/cross_validate.py` in the workspace.
- [x] 1.2 Import all necessary modules including pandas, numpy, torch, DictionaryMatcher, and DataCleaner.

## 2. 3-Way Prediction Evaluation Implementation

- [x] 2.1 Load and split the 10% test data from `dataset/HQ 2025.xlsx` consistently with the error analysis script.
- [x] 2.2 Initialize the two `DictionaryMatcher` instances for DICT_HQ_2026 and dictv3.
- [x] 2.3 Initialize `DataCleaner` and load the fine-tuned multitask PhoBERT model.
- [x] 2.4 Run predictions across the test dataset for all three models (DICT_HQ_2026 with HS filter, dictv3, PhoBERT multitask).

## 3. Disagreement Pattern Classification & Reporting

- [x] 3.1 Implement the logic to classify predictions into the 5 pattern categories based on mismatch/agreement configurations.
- [x] 3.2 Implement reporting logic to generate `cross_validation_report.csv`, `dict_fixes_needed.csv`, and `hard_cases.csv` under `analysis/output/`.
- [x] 3.3 Print a summary report showing the counts and percentages for each pattern.
