## MODIFIED Requirements

### Requirement: Hybrid Product Classification
The system SHALL classify products by first executing a dictionary-based pass (`dictv2.csv` or `dictv3.csv`) using a high-performance Aho-Corasick automaton. The system SHALL then gather all products that failed to meet the dictionary threshold and process them using the PhoBERT AI model in batched operations (e.g., batch size 64) instead of row-by-row.

#### Scenario: Dictionary Match with High Confidence
- **WHEN** a product description is processed in the global dictionary pass and matches keywords in the dictionary to achieve a score above the predefined threshold
- **THEN** the system assigns the product's category directly from the dictionary mapping and excludes it from the subsequent AI batch pass.

#### Scenario: Fallback to AI Model in Batches
- **WHEN** a subset of product descriptions do not achieve a sufficient dictionary score
- **THEN** the system groups these product descriptions into batches and invokes the PhoBERT sequence classification model to predict the product categories efficiently, before merging the results back into the main dataset.
