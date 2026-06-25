## ADDED Requirements

### Requirement: Keyword Purity and Quality Scoring
The `DictionaryGenerator` SHALL analyze historical HS code data to generate high-quality keywords for each Lớp 1 and Lớp 2. The generation MUST incorporate statistical purity (Term Frequency / Global Frequency), but MUST apply Contextual Filters and Global Stopwords BEFORE calculating purity to prevent statistical anomalies caused by overlapping generic terms.

#### Scenario: End-to-End Extraction with Filtering
- **WHEN** the generator processes a group of products for "Đèn côn trùng" that frequently contains the phrase "mặt trời hiệu"
- **THEN** the generator first checks the n-gram against `GLOBAL_STOPWORDS` (detecting "hiệu") and `CONTEXT_RESTRICTED` (detecting "mặt trời" out of context), immediately discards it, and selects the next highest scoring legitimate keyword (e.g. "bẫy côn trùng") instead.
