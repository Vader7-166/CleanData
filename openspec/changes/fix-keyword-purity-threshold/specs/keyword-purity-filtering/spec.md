## ADDED Requirements

### Requirement: Keyword Purity Threshold
The system SHALL filter out any candidate keyword whose local purity (`class_frequency / global_frequency`) is less than 0.2 (20%) before adding it to the final keyword list for a category.

#### Scenario: High Purity Keyword Extraction
- **WHEN** an n-gram appears in a category and has a purity score of 0.8 (appears mostly in this category).
- **THEN** the system includes it as a candidate and may select it as one of the top keywords.

#### Scenario: Low Purity Keyword Exclusion
- **WHEN** an n-gram appears in a category but has a purity score of 0.05 (e.g., a generic brand name appearing predominantly in other categories).
- **THEN** the system completely excludes it from the candidate pool for this category, even if the category has fewer than `top_n` (12) total candidate keywords.
