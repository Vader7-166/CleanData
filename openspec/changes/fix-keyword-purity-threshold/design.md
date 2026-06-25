## Context

The system currently groups raw product descriptions by `Mã HS` and sub-categories (`Lớp 1`, `Lớp 2`, etc.), then extracts the top 12 distinguishing n-grams using a TF-IDF variant algorithm. This algorithm calculates a local Purity score `p` for each n-gram (`class_frequency / global_frequency`).
However, because it forces the selection of exactly `top_n=12` keywords, it ends up including n-grams with negligible Purity scores if a category lacks linguistic diversity. This results in generic brand names (like "Rạng Đông") or generic components (like "đèn đi ốt") becoming keywords for unrelated classifications, completely breaking the `DictionaryMatcher` downstream.

## Goals / Non-Goals

**Goals:**
- Eliminate the extraction of low-purity, generic n-grams as keywords.
- Guarantee that any keyword assigned to a category actually represents a meaningful proportion (>= 20%) of that n-gram's global occurrences.
- Fix downstream misclassifications in the cleaning pipeline.

**Non-Goals:**
- Completely rewriting the TF-IDF logic or changing the NLP pipeline.
- Modifying the downstream `DictionaryMatcher` algorithm.

## Decisions

**Decision 1: Implement a Hard Purity Threshold**
- **Rationale**: By enforcing `p >= 0.2` (the n-gram must belong to this specific class at least 20% of the times it appears globally), we guarantee that the n-gram is distinctive. If an n-gram is overwhelmingly used by other categories (e.g., `p = 0.01`), it cannot represent this category, regardless of how often it appears within this specific category.
- **Alternatives Considered**: 
  - Using a hardcoded Stopword list: Rejected because maintaining an exhaustive list of generic words and brand names is impossible and not scalable.
  - Making `DictionaryMatcher` aware of `Mã HS`: Rejected as it doesn't solve the core issue of dirty keywords (e.g. `85395290` contains both `đèn côn trùng` and `led khác`, so `Mã HS` filtering wouldn't separate them).

## Risks / Trade-offs

- **[Risk] Categories losing all keywords**: If a category's descriptions consist *entirely* of generic terms without any distinguishing features, it might return 0 keywords.
  - **Mitigation**: This is actually the desired behavior! If a group has no distinguishing keywords, it *should not* artificially claim generic keywords. This will accurately result in the `DictionaryMatcher` falling back to other strategies or marking it as "Cần kiểm tra" rather than confidently misclassifying it.
