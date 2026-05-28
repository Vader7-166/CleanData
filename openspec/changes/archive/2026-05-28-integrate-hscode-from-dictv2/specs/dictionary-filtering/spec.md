## MODIFIED Requirements

### Requirement: Hybrid Product Classification
The system SHALL classify products by first executing a dictionary-based pass (using `dictv2.csv` or the active dictionary from `dataset/`) using pre-compiled regular expressions. The system SHALL then gather all products that failed to meet the dictionary threshold and process them using the PhoBERT AI model in batched operations (e.g., batch size 32) instead of row-by-row.

#### Scenario: Dictionary Match with High Confidence
- **WHEN** a product description is processed in the global dictionary pass and matches pre-compiled keywords in the active dictionary to achieve a score above the predefined threshold
- **THEN** the system assigns the product's category (Dòng SP, Loại, Lớp 1, Lớp 2) and HS CODE (Mã HS) directly from the dictionary mapping and excludes it from the subsequent AI batch pass.

#### Scenario: Fallback to AI Model in Batches
- **WHEN** a subset of product descriptions do not achieve a sufficient dictionary score
- **THEN** the system groups these product descriptions into batches and invokes the PhoBERT sequence classification model to predict the product categories efficiently, before merging the results back into the main dataset.
