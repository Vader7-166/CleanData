## ADDED Requirements

### Requirement: 3-Way Prediction Alignment
The analysis script SHALL load the 10% test split from `dataset/HQ 2025.xlsx` and evaluate it against three prediction paths: DICT_HQ_2026 (using HS filter), dictv3, and the PhoBERT multitask model.

#### Scenario: Running 3-way prediction evaluation
- **WHEN** the user executes the cross-validation script
- **THEN** the script loads the test dataset and runs predictions through the new dictionary matcher, old dictionary matcher, and the PhoBERT multitask classifier.

### Requirement: Pattern Classification
The script SHALL classify each disagreement/agreement pattern between the predictions and the ground truth into five distinct categories to determine necessary actions.

#### Scenario: Categorizing prediction patterns
- **WHEN** the three prediction outputs are obtained
- **THEN** the script classifies each sample according to the 5 mismatch patterns:
  - Pattern 1: Dict_HQ and dictv3 are correct, AI is incorrect (AI needs more training samples)
  - Pattern 2: Dict_HQ is correct, AI and dictv3 are incorrect (Dict_HQ superior)
  - Pattern 3: AI is correct, Dict_HQ and dictv3 are incorrect (AI stronger)
  - Pattern 4: All 3 predictions are incorrect (Hard case for manual review)
  - Pattern 5: Dict_HQ and AI are correct, dictv3 is incorrect (Deprecate dictv3 entry)

### Requirement: Report Output Generation
The script SHALL generate three CSV files under `analysis/output/` summarizing the disagreements, dictionary fixes needed, and hard cases.

#### Scenario: Creating analysis output CSV files
- **WHEN** the classification of patterns is complete
- **THEN** the script writes `cross_validation_report.csv`, `dict_fixes_needed.csv`, and `hard_cases.csv` to the output directory.
