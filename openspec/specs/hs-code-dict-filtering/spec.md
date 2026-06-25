# hs-code-dict-filtering Specification

## Purpose
TBD - created by archiving change phase2-hs-dict-integration. Update Purpose after archive.
## Requirements
### Requirement: HS code prefix filtering in DictionaryMatcher

DictionaryMatcher SHALL support optional HS code filtering during prediction. When an `hs_code` parameter is provided, only dictionary rows whose `Mã HS` shares the same 4-digit prefix SHALL be considered for scoring. When `hs_code` is None or empty, all dictionary rows SHALL be considered (backward compatible).

#### Scenario: HS code provided, match found in filtered subset
- **WHEN** `predict(text="đèn led bulb", hs_code="85391010")` is called
- **THEN** only dictionary rows with `Mã HS` starting with `8539` are scored
- **AND** matching rows from HS `9405` are excluded from consideration

#### Scenario: HS code not provided, all rows considered
- **WHEN** `predict(text="đèn led bulb")` is called without hs_code
- **THEN** all dictionary rows are scored (existing behavior preserved)

#### Scenario: HS code provided but no matching prefix
- **WHEN** `predict(text="đèn led bulb", hs_code="9999xxxx")` is called
- **THEN** no dictionary rows match the HS prefix
- **AND** the method returns `[None, 0.0, "Cần kiểm tra"]`

### Requirement: Worker passes HS code to dictionary matcher

The `process_chunk()` function SHALL accept `Mã HS` column from the input chunk and pass each row's HS code to `matcher.predict(text, hs_code=hs_code)`.

#### Scenario: Chunk with HS codes processed
- **WHEN** a chunk containing `['Tên hàng raw', 'Mã HS']` columns is processed
- **THEN** each row's HS code is extracted and passed to the dictionary matcher
- **AND** rows without HS codes fall back to full dict matching

### Requirement: HS taxonomy pre-classification

The `process_async()` pipeline SHALL lookup HSTaxonomy for each row's `Mã HS` before running dictionary matching. When a taxonomy match is found AND the corresponding dictionary row has `Số lượng SP > 100`, the pipeline SHALL pre-fill `Dòng SP` and `Loại` columns.

#### Scenario: HS code matches taxonomy with high confidence
- **WHEN** a row has `Mã HS = "85391010"` AND HSTaxonomy has a matching prefix
- **AND** DICT_HQ_2026 has a row for this HS with `Số lượng SP > 100`
- **THEN** `Dòng SP` and `Loại` are pre-filled from the dict row
- **AND** the dict/AI pipeline fills remaining `Lớp 1` and `Lớp 2`

#### Scenario: HS code not in taxonomy or low frequency
- **WHEN** a row has `Mã HS` not found in HSTaxonomy or `Số lượng SP <= 100`
- **THEN** no pre-filling occurs
- **AND** the normal dict → AI fallback chain proceeds

### Requirement: New fallback chain order

The classification pipeline SHALL follow this priority order: (1) HS taxonomy pre-classification for Dòng SP + Loại, (2) HS-filtered dictionary matching, (3) AI model inference, (4) "Cần kiểm tra" fallback.

#### Scenario: Complete classification through fallback chain
- **WHEN** an input row is processed
- **THEN** HS taxonomy is checked first for Dòng SP and Loại
- **AND** if not auto-filled, HS-filtered dict matching is attempted
- **AND** if dict fails, AI model is invoked
- **AND** if AI confidence < 0.85, status is "Cần kiểm tra"

