## Context

The dictionary matching pass (Pass 1) in the classification pipeline uses the Aho-Corasick algorithm to search for thousands of keywords across millions of characters of product descriptions. The effectiveness of this pass depends on how keywords are curated, scored, and mapped to labels. Currently, dictionary files like `dictv2.csv` and `dictv3.csv` are used, but their structure and requirements are not formally documented, leading to potential inconsistencies when new entries are added.

## Goals / Non-Goals

**Goals:**
- Define a strict schema for the dictionary CSV file.
- Specify normalization rules for keywords to ensure they match the pipeline's cleaning logic.
- Document the scoring mechanism (High Value vs. Regular vs. Junk) within the dictionary context.
- Provide a guide for optimizing keywords (e.g., avoiding overly broad keywords that cause false positives).

**Non-Goals:**
- Developing a UI for dictionary management (covered in other specs).
- Changing the underlying Aho-Corasick implementation.

## Decisions

### 1. File Format and Encoding
- **Decision**: Use CSV format with `utf-8-sig` (UTF-8 with BOM) encoding.
- **Rationale**: CSV is easily editable in Excel (a common tool for domain experts). `utf-8-sig` ensures that Vietnamese characters are handled correctly by Excel without manual configuration.

### 2. Mandatory Columns
- **Decision**: The dictionary MUST contain: `Keyword`, `Dòng SP`, `Loại`, `Lớp 1`, `Lớp 2`, `Mã HS`.
- **Rationale**: These columns map directly to the system's output schema. Providing a complete mapping at the dictionary level reduces the need for secondary logic.

### 3. Keyword Normalization
- **Decision**: Keywords in the dictionary must be lowercased and stripped of special characters, matching the `clean_text_for_dict` function in the backend.
- **Rationale**: This ensures a 1:1 match between the pre-processed product description and the dictionary keywords.

### 4. Keyword Comma-Separated List
- **Decision**: The `Keyword` column can contain multiple keywords separated by commas.
- **Rationale**: Allows multiple triggers to map to the same set of labels, reducing row redundancy.

## Risks / Trade-offs

- **[Risk] Overlapping Keywords** → A broad keyword (e.g., "đèn") matching alongside a specific one (e.g., "đèn âm trần").
  - **Mitigation**: The system uses length-based scoring and a "consumption" logic where longer/more specific matches are preferred.
- **[Risk] Performance with Extremely Large Dictionaries** → Aho-Corasick memory usage grows with the number of keywords.
  - **Mitigation**: Monitor memory usage; the current scale (~thousands of keywords) is well within limits.
