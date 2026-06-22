## ADDED Requirements

### Requirement: Accuracy breakdown by classification level

The system SHALL compute accuracy separately for each of the 4 classification levels (`Dòng SP`, `Loại`, `Lớp 1`, `Lớp 2`) by splitting the combined label `"Dòng SP | Loại | Lớp 1 | Lớp 2 | Mã HS"` and comparing each component with ground truth.

#### Scenario: All levels have high accuracy
- **WHEN** predictions are run on a test set with known ground truth
- **THEN** four separate accuracy scores are calculated and reported: one for Dòng SP, one for Loại, one for Lớp 1, and one for Lớp 2

#### Scenario: One level has significantly lower accuracy
- **WHEN** Lớp 2 accuracy is significantly lower than other levels
- **THEN** the report highlights which level is the bottleneck for improvement

### Requirement: Confusion matrix visualization

The system SHALL generate a heatmap visualization of the top-20 most confused class pairs using matplotlib, based on actual prediction vs ground truth comparison at the combined label level.

#### Scenario: Generate confusion heatmap
- **WHEN** error analysis is run
- **THEN** a PNG image file is saved showing a labeled heatmap of the 20 class pairs with highest confusion counts

### Requirement: Top confused class pairs listing

The system SHALL output a ranked list of the top-10 class pairs that are most frequently confused, including the count of confusions for each pair.

#### Scenario: Export confused pairs
- **WHEN** error analysis completes
- **THEN** a CSV file is saved with columns: `ground_truth`, `predicted`, `count`, sorted by count descending, limited to top 10 rows

### Requirement: Dictionary vs AI performance comparison

The system SHALL compare the performance of DictionaryMatcher and AI model on the same test set, reporting: percentage of rows handled by each, accuracy of each, and overlap analysis (both correct, both wrong, dict correct + AI wrong, dict wrong + AI correct).

#### Scenario: Dict handles majority of inputs
- **WHEN** dictionary matching produces scores above the threshold for most inputs
- **THEN** the report shows dict coverage percentage, dict accuracy, and AI fallback accuracy separately

#### Scenario: Overlap analysis
- **WHEN** both dict and AI predictions are available for all test rows
- **THEN** four overlap categories are counted and reported: both correct, both wrong, dict-only correct, AI-only correct

### Requirement: Calibration curve with confidence bins

The system SHALL divide AI prediction confidence scores into bins (0-0.5, 0.5-0.6, 0.6-0.7, 0.7-0.8, 0.8-0.85, 0.85-0.9, 0.9-0.95, 0.95-1.0), compute actual accuracy within each bin, and generate a calibration curve plot. The system SHALL also identify the optimal confidence threshold where actual accuracy begins to degrade.

#### Scenario: Model is well-calibrated
- **WHEN** confidence scores closely match actual accuracy across all bins
- **THEN** the calibration curve shows a near-diagonal line and the current threshold (0.85) is confirmed as reasonable

#### Scenario: Model is overconfident
- **WHEN** confidence scores are consistently higher than actual accuracy
- **THEN** the calibration curve bends below the diagonal and the report suggests a higher optimal threshold

### Requirement: No modification to production code

The analysis script SHALL NOT modify any production pipeline code (`data_cleaner.py`, `dictionary_matcher.py`, `dict_generator.py`). It SHALL import and reuse existing classes and functions from the backend.

#### Scenario: Script runs independently
- **WHEN** `analysis/error_analysis.py` is executed
- **THEN** it imports DataCleaner, DictionaryMatcher, and utility functions from `backend/` without changing them

### Requirement: CPU-only execution

The analysis SHALL run entirely on CPU without requiring GPU resources.

#### Scenario: Run on CPU server
- **WHEN** the script is executed on a server without CUDA
- **THEN** all predictions (dict and AI) complete successfully using CPU-only inference
