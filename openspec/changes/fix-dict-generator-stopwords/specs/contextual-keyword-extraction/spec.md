## ADDED Requirements

### Requirement: Global Stopword Filtering
The system SHALL filter out any extracted keyword n-gram that contains any generic term or brand name defined in the `GLOBAL_STOPWORDS` list.

#### Scenario: Blocking a Brand Name
- **WHEN** the dictionary generator extracts the candidate n-gram "led hiệu philips"
- **THEN** the system identifies the stopword "philips" in the `GLOBAL_STOPWORDS` list, immediately rejects the candidate, and prevents it from being added to the dictionary.

### Requirement: Context-Restricted Keywords
The system SHALL define a `CONTEXT_RESTRICTED` map containing keywords that are only valid when the product's category (`Lớp 1` or `Lớp 2`) semantically matches the required context.

#### Scenario: Blocking an Out-of-Context Keyword
- **WHEN** the dictionary generator evaluates the n-gram "năng lượng mặt trời" for a group of products whose `Lớp 1` is "đèn côn trùng"
- **THEN** the system determines that "năng lượng mặt trời" requires a solar context, rejects the candidate, and does not assign it to "đèn côn trùng".

#### Scenario: Approving an In-Context Keyword
- **WHEN** the dictionary generator evaluates the n-gram "năng lượng mặt trời" for a group of products whose `Lớp 1` is "đèn năng lượng mặt trời"
- **THEN** the system determines that the context is valid and allows the n-gram to proceed to TF-IDF scoring.
