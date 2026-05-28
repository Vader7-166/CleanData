# Proposal: Refine HS Crawler Accuracy

Improve the accuracy of crawled HS taxonomy descriptions by refining the DeepSeek LLM prompt and updating the fallback regex parsing logic to prevent heading-level descriptions from leaking into 8-digit sub-heading fields.

## Problem Statement

When querying HS codes (e.g. `90012000` or `74061000`), the crawled Level 1 (industry_name) descriptions are occasionally inaccurate. Instead of specific subheading leaf-node descriptions (e.g. "Tấm và bản bằng vật liệu phân cực"), they return the parent 4-digit heading level descriptions (e.g. "Thấu kính, lăng kính..."). This is caused by:
1. The fallback regex pattern in `_crawl_hscode_pro` matching the 4-digit prefix instead of the full 8-digit code.
2. The DeepSeek LLM prompt not explicitly instructing the model to distinguish between the parent Heading title and the specific Subheading item description.

## Proposed Scope

1. **Refine DeepSeek LLM Prompt**: Instruct the model to strictly distinguish the 4-digit Heading level (parent) from the 8-digit leaf node description (subheading). Provide clear instructions to prevent the model from repeating parent group text as the specific product name.
2. **Improve Fallback Regex**: Update the fallback search pattern in `_crawl_hscode_pro` to use the full `hs_code` rather than slicing it to `hs_code[:4]` when searching for detailed descriptions.
3. **Verify Crawler Output**: Re-run testing scripts inside the Docker container to verify accuracy on known edge cases (e.g., `90012000`, `74061000`).
