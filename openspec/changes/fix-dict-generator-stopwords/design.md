## Context

Currently, the `extract_keywords_ai` function in `backend/core/dict_generator.py` uses purely statistical metrics (Term Frequency and Purity) to select keywords for each product category (Lớp 1, Lớp 2). While this works for highly distinctive terms, it fails for generic terms or brand names that happen to co-occur frequently within a specific subset of products. For instance, if 49 "đèn côn trùng" happen to include the brand phrase "mặt trời hiệu JINDIAN", the statistical purity of "mặt trời hiệu" exceeds the 5% threshold, causing the dictionary to link "mặt trời hiệu" to "đèn côn trùng".

## Goals / Non-Goals

**Goals:**
- Implement a `GLOBAL_STOPWORDS` list to completely block generic terms, specs, and brand names from becoming dictionary keywords.
- Implement a `CONTEXTUAL_KEYWORDS` map where specific terms (e.g. "mặt trời", "solar") are only allowed if the target category semantically relates to them.
- Clean up existing dirty tokens before they reach the TF-IDF and Purity calculation logic.

**Non-Goals:**
- Removing the Aho-Corasick matching logic (already updated with HS-awareness in previous change).
- Training a new machine learning model for keyword extraction.

## Decisions

**1. Static Stopword and Context Lists:**
- Define `GLOBAL_STOPWORDS = {'hiệu', 'công suất', 'kích thước', 'jindian', 'philips', 'gp', 'rạng đông', 'điện quang', 'panasonic', 'samsung', 'lg', 'toshiba'}`. Any n-gram containing these tokens will be instantly rejected.
- Define `CONTEXT_RESTRICTED = {'mặt trời': 'năng lượng mặt trời', 'solar': 'năng lượng mặt trời', 'nlmt': 'năng lượng mặt trời'}`. If an n-gram contains "mặt trời", it will be rejected UNLESS the target category (`Lớp 1` or `Lớp 2`) contains "năng lượng mặt trời" or "solar".
- **Rationale**: A rule-based approach is extremely fast, transparent, and exactly targets the anomalies observed in the data without risking the performance of the statistical purity logic.

**2. Where to Apply the Filters:**
- The filtering will be applied inside the `extract_keywords_ai` function of `backend/core/dict_generator.py`, specifically inside the loop that iterates over candidate n-grams (`for n, lf in class_f[i].items():`).
- **Rationale**: Filtering before scoring saves computation time and prevents junk candidates from participating in the overlap-prevention logic.

## Risks / Trade-offs

- **[Risk] Missing Valid Keywords**: Some generic stopwords might accidentally form part of a valid multi-word keyword (e.g., "đèn hiệu ứng").
  - **Mitigation**: Keep the `GLOBAL_STOPWORDS` list strictly focused on unambiguous junk words and common brands. Words like "hiệu" (brand) are distinct from "hiệu ứng" (effect) if tokenization is handled correctly, but we must be careful. We will filter based on exact whole words, not substrings (e.g., `if 'hiệu' in words`).
