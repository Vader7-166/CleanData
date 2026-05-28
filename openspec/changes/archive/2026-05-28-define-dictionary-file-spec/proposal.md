## Why

The current data processing pipeline relies heavily on a dictionary-based pass for classification. To ensure maximum accuracy and performance (especially with the Aho-Corasick optimization), a formal specification for the dictionary file format is required. This ensures that the dictionary is structured in a way that the processing logic can consume efficiently and accurately.

## What Changes

- Create a comprehensive specification for the dictionary CSV format (`dictv3.csv` and future versions).
- Define mandatory and optional columns.
- Establish rules for keyword formatting, normalization, and scoring.
- Document the relationship between dictionary entries and the final output columns.

## Capabilities

### New Capabilities
- `dictionary-format-spec`: A detailed specification defining the schema, validation rules, and optimization guidelines for dictionary files used in the classification pipeline.

### Modified Capabilities
- `dictionary-filtering`: Update the existing requirement to refer to the new formal dictionary specification.

## Impact

- `backend/core/data_cleaner.py`: Validation logic might be added to check the dictionary format against the spec.
- `dataset/`: Dictionary files in this directory must adhere to the new specification.
- Documentation: Provides a clear guide for users or developers adding new keywords to the system.
