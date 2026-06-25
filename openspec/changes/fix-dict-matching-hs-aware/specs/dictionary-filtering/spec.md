## MODIFIED Requirements

### Requirement: Hybrid Product Classification
The system SHALL classify products by first executing a dictionary-based pass using pre-compiled regular expressions and Aho-Corasick automaton. The dictionary matching MUST be context-aware, incorporating the product's `Mã HS` (HS Code) to filter matches. The system SHALL then gather all products that failed to meet the dictionary threshold and process them using the PhoBERT AI model in batched operations (e.g., batch size 32) instead of row-by-row.

#### Scenario: Dictionary Match with High Confidence and HS Code Match
- **WHEN** a product description is processed in the global dictionary pass, matches pre-compiled keywords, AND the product's 4-digit HS prefix matches the dictionary entry's 4-digit HS prefix
- **THEN** the system retains the full match score, and if it is above the predefined threshold, assigns the product's category directly from the dictionary mapping, excluding it from the AI pass.

#### Scenario: Dictionary Match with HS Code Mismatch
- **WHEN** a product description matches pre-compiled keywords, BUT the product's 4-digit HS prefix does NOT match the dictionary entry's 4-digit HS prefix
- **THEN** the system heavily penalizes or discards the match score, forcing the product to be processed by the fallback AI model.

#### Scenario: Dictionary Match with Missing HS Code
- **WHEN** a product description matches pre-compiled keywords, BUT the product's HS Code is missing or invalid
- **THEN** the system bypasses the HS-aware filter and evaluates the match based purely on the text substring score.

#### Scenario: Fallback to AI Model in Batches
- **WHEN** a subset of product descriptions do not achieve a sufficient dictionary score
- **THEN** the system groups these product descriptions into batches and invokes the PhoBERT sequence classification model to predict the product categories efficiently, before merging the results back into the main dataset.
