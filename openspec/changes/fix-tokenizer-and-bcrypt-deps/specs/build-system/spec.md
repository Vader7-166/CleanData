## ADDED Requirements

### Requirement: Tokenizer Backend Support
The backend environment MUST have all necessary libraries for the PhoBERT tokenizer to initialize.

#### Scenario: Successful tokenizer load
- **WHEN** the `AutoTokenizer.from_pretrained(model_path)` is called
- **THEN** it SHALL NOT raise an `ImportError` for `protobuf` or `ValueError` for `sentencepiece`

### Requirement: Compatible Password Hashing
The backend environment SHALL use a version of `bcrypt` that is fully compatible with the installed version of `passlib`.

#### Scenario: Admin user creation
- **WHEN** the `startup_event` hashes the admin password
- **THEN** it SHALL NOT raise an `AttributeError` for `bcrypt.__about__`
