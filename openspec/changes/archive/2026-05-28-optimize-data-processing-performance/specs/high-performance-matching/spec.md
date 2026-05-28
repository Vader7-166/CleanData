## ADDED Requirements

### Requirement: Aho-Corasick Keyword Matching
The system SHALL utilize the Aho-Corasick algorithm for dictionary keyword matching to ensure O(N) time complexity regardless of the number of keywords.

#### Scenario: Efficient multi-keyword matching
- **WHEN** a product description contains multiple potential dictionary keywords
- **THEN** the system identifies all matches in a single pass over the text
- **THEN** the system applies a "consumption" logic where longer matches have priority over shorter ones to prevent overlapping match conflicts.

### Requirement: Weighted Keyword Scoring
The system SHALL calculate a match score based on keyword priority (High Value, Regular, or Junk) to determine the best dictionary mapping.

#### Scenario: Priority-based classification
- **WHEN** multiple dictionary mappings match the input text
- **THEN** keywords marked as "High Value" contribute more significantly (e.g., 20 points) to the total score than regular keywords (length-based scoring)
- **THEN** "Junk" keywords are consumed but contribute zero points to the score.
