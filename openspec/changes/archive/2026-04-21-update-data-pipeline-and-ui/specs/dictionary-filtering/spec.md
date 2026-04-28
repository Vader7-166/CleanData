## ADDED Requirements

### Requirement: Hybrid Product Classification
The system SHALL classify products by first using a dictionary-based approach (`dictv3.csv` located in `dataset/`) and high-weight words, falling back to an AI model if the dictionary confidence is low.

#### Scenario: Dictionary Match with High Confidence
- **WHEN** a product description matches keywords in `dictv3` and achieves a score above the predefined threshold (e.g., matching high-weight words worth 20 points)
- **THEN** the system assigns the product's category (`Dòng SP`, `Loại`, `Lớp 1`, `Lớp 2`) directly from the dictionary mapping without invoking the AI model.

#### Scenario: Fallback to AI Model
- **WHEN** a product description does not achieve a sufficient dictionary score
- **THEN** the system invokes the PhoBERT sequence classification model to predict the product categories.
