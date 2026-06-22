## ADDED Requirements

### Requirement: Keyword Extraction Scoring Algorithm
The keyword extraction algorithm MUST implement the scoring formula exactly as documented:
`score = local_freq * (purity^2) * base_score`
Where `base_score` is the number of words in the n-gram.
High-value keywords (e.g., 'năng lượng mặt trời', 'nlmt', 'solar') MUST receive an additional 20 points to their `base_score`.
1-grams MUST have their final `score` multiplied by 0.5 to penalize short keywords.

#### Scenario: Scoring a high-value n-gram
- **WHEN** an n-gram contains "năng lượng mặt trời"
- **THEN** its base_score is increased by 20 before the final score calculation

#### Scenario: Scoring a 1-gram
- **WHEN** an n-gram consists of exactly 1 word
- **THEN** its final score is reduced by 50%

### Requirement: Keyword Purity Threshold
The purity of a keyword (local frequency / global frequency) MUST be at least 5% (0.05) to be considered for selection.

#### Scenario: Low purity filtering
- **WHEN** a keyword's purity is below 0.05
- **THEN** it is filtered out and not included in the dictionary

### Requirement: Overlap Prevention
The algorithm MUST prioritize longer n-grams. When filtering the top N keywords, if a shorter keyword is a substring of an already selected longer keyword, it is ignored. If a shorter keyword is already in the selected list and a new, longer keyword containing the shorter one is processed, the longer keyword MUST replace the shorter one or be added while the shorter one is removed.

#### Scenario: Longer n-gram supersedes shorter n-gram
- **WHEN** the top keywords list contains "đèn led" and "đèn led âm trần" is being evaluated
- **THEN** "đèn led âm trần" is added and "đèn led" is removed from the top keywords list

### Requirement: Multi-word Token Validation
Validation of n-grams MUST NOT reject multi-word strings simply because the first word starts with a number. The `_is_valid_cluster_token` function MUST only be applied to individual words within the n-gram, or the logic updated to allow numeric prefixes in n-grams (e.g., "10w âm trần").

#### Scenario: N-gram with leading number
- **WHEN** the n-gram "10w âm trần" is evaluated
- **THEN** it is accepted as a valid keyword string
