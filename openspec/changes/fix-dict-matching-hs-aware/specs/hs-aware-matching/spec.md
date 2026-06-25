## ADDED Requirements

### Requirement: HS-Aware Match Filtering
The `DictionaryMatcher` SHALL use the product's HS Code (`Mã HS`) to contextualize and validate Aho-Corasick substring matches. The matcher MUST store the origin HS Code of every dictionary entry and perform a validation step during the scoring phase.

#### Scenario: Validating Match with Exact 4-Digit HS Prefix
- **WHEN** a product is being evaluated by the `DictionaryMatcher` and has an HS Code of `94054990`
- **AND** it matches a dictionary entry that originated from HS Code `94054190`
- **THEN** the system extracts the 4-digit prefixes (`9405` and `9405`), determines they match, and retains the full score for this dictionary match.

#### Scenario: Invalidating Match across Different HS Families
- **WHEN** a product is being evaluated by the `DictionaryMatcher` and has an HS Code of `85395290`
- **AND** it matches a dictionary entry that originated from HS Code `94054190`
- **THEN** the system extracts the 4-digit prefixes (`8539` and `9405`), determines they do NOT match, and penalizes or discards the score for this dictionary match.

#### Scenario: Handling Missing Input HS Code
- **WHEN** a product is being evaluated by the `DictionaryMatcher` but its HS Code is empty, null, or less than 4 digits long
- **THEN** the system bypasses the HS validation step and retains the full score for any dictionary match.
