## Why

The current dictionary generation algorithm in `backend/core/dict_generator.py` contains several critical logical flaws that deviate from the documented specifications in `SYSTEM_DOCUMENTATION.md`. These flaws result in a poor-quality dictionary with overly generic keywords, missed high-value specific keywords, and inaccurate scoring, which directly degrades the performance of the downstream Aho-Corasick matching system. 

Specifically:
1. Overlap prevention incorrectly discards longer, more specific n-grams if shorter n-grams have higher scores.
2. The scoring formula uses square roots instead of the direct word count, lacks the +20 multiplier for High Value keywords, and does not penalize 1-grams by 50%.
3. The purity threshold is set to 20% instead of the documented 5%, causing valid specific keywords to be unfairly discarded in large clusters.
4. Token validation is incorrectly applied to entire n-grams, causing n-grams starting with numbers (e.g., "10w âm trần") to be rejected.

## What Changes

- **Rewrite Keyword Extraction Scoring**: Implement the exact formula `score = local_freq × purity² × base_score` (where base_score = word count, +20 for High Value keywords, and -50% for 1-grams).
- **Fix Overlap Prevention Logic**: Sort candidates by n-gram length descending first, then score. Ensure longer n-grams are kept and shorter overlapping n-grams are discarded.
- **Adjust Purity Threshold**: Lower the purity threshold from `0.2` (20%) to `0.05` (5%) to align with the documentation.
- **Fix Token Validation**: Remove the single-token validation from entire n-grams, ensuring multi-word n-grams and numeric prefixes are processed correctly.

## Capabilities

### New Capabilities
- `dict-generation-fix`: Correcting the NLP extraction logic and overlap prevention in the dictionary generator to match the specified algorithm.

### Modified Capabilities

## Impact

- `backend/core/dict_generator.py`: The `extract_keywords_ai` method will be heavily refactored.
- Downstream dictionary quality will improve significantly, resulting in much higher auto-classification rates.
