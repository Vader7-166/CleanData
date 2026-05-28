## ADDED Requirements

### Requirement: Multi-Dictionary Automaton Generation
The system SHALL support combining multiple active dictionaries into a single Aho-Corasick automaton for high-performance (O(N)) text matching during the data cleaning phase.

#### Scenario: Dictionary Loading
- **WHEN** the cleaning pipeline initializes the text matcher
- **THEN** it reads all dictionaries marked as active and builds a single unified Aho-Corasick trie.

### Requirement: Admin Priority Conflict Resolution
The system SHALL resolve keyword conflicts across multiple dictionaries by giving strict priority to dictionaries created by Administrators.

#### Scenario: Keyword Conflict
- **WHEN** two active dictionaries define different HS codes for the exact same keyword, and one dictionary belongs to an Admin while the other belongs to a regular User
- **THEN** the system overwrites the User's mapping with the Admin's mapping in the final automaton.
