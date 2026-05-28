## 1. Implement Crawler Optimizations

- [x] 1.1 Refine the DeepSeek Prompt in `crawler.py` to add strict guidelines distinguishing 4-digit Heading level vs 8-digit Subheading level.
- [x] 1.2 Modify the regex pattern in `_crawl_hscode_pro` to search for the full `hs_code` instead of slicing it to the 4-digit prefix.

## 2. Verification

- [x] 2.1 Update `backend/core/test_crawler.py` to add test cases for `90012000` and `74061000`.
- [x] 2.2 Run the test crawler script inside the backend container and verify that both codes return correct detailed descriptions.
