## 1. Base Scoring & Purity Threshold Updates

- [x] 1.1 In `backend/core/dict_generator.py`, locate the `extract_keywords_ai` method.
- [x] 1.2 Update the purity check from `p < 0.2` to `p < 0.05` to match the documented threshold.
- [x] 1.3 Calculate `base_score = len(n.split())`.
- [x] 1.4 Add `high_value_kws = {'năng lượng mặt trời', 'solar', 'nlmt'}` and grant a +20 bonus to `base_score` if any match.
- [x] 1.5 Update the final score calculation to use direct multiplication instead of square roots: `score = lf * (p**2) * base_score`.
- [x] 1.6 Add logic to multiply the final score by `0.5` if `len(n.split()) == 1`.

## 2. Token Validation Adjustments

- [x] 2.1 Remove the `_is_valid_cluster_token(n)` call directly on the entire n-gram `n`.
- [x] 2.2 Reimplement token validity check so it iterates over `n.split()` or relies exclusively on the earlier `tokenize_vi` stage to clean invalid single tokens, allowing valid multi-word n-grams starting with a number.

## 3. Overlap Prevention Logic

- [x] 3.1 Sort the `cands` array using `lambda x: (len(x[0].split()), x[1])` in reverse order so longer n-grams with higher scores come first.
- [x] 3.2 Update the overlap tracking logic: Check if the new `clean_w` is a substring of any word currently in `top`. If so, skip it.
- [x] 3.3 Update the overlap tracking logic: Filter out any existing strings in `top` that are substrings of the new `clean_w`, and append `clean_w` to `top`.
- [x] 3.4 Ensure the length of `top` adheres to the `top_n` limit appropriately, considering items might be removed during processing.

## 4. Verification

- [x] 4.1 Run the `test_dictionary_gen.py` script to generate a new dictionary.
- [x] 4.2 Validate the keywords output in `scratch/test_dictionary_gen_out.txt` and verify that multi-word strings like "đèn led âm trần" and high-value keywords are correctly populated in the `NEW_DICT.csv`.
