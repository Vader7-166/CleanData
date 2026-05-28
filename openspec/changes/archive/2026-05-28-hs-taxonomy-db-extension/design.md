## Context

Currently, the system uses dictionaries for data cleaning, but there is no centralized database table that maps HS codes to industry taxonomies (HS_TAXONOMY) and default classifications. Moving this mapping to the database, supplemented by an online crawler and manual validation UI, allows for automated, dynamic categorization without code redeployments.

## Goals / Non-Goals

**Goals:**
- Create a persistent mapping between HS codes (or prefixes) and their corresponding Lớp 1 (Industry), Dòng sản phẩm (Product Line), and Loại (NC/LK).
- Automatically lookup unknown HS codes online using a web crawler.
- Provide a manual intervention UI in the Dictionary Generator Wizard when automatic crawling fails to resolve an HS code.
- Provide a dedicated management page for CRUD operations on HS Taxonomies.

**Non-Goals:**
- Completely replacing the dictionary-based matching logic (rather, this enriches dictionary drafts and final clean outputs).

## Decisions

- **Decision 1: Extended Reference Table (`HSTaxonomy`)**:
  - Columns:
    - `id`: Integer primary key.
    - `hs_code_prefix`: String (e.g., "70200030" or "8539"), representing the HS code or prefix. Unique constraint.
    - `dong_sp`: String (e.g., "SP ĐÈN/BÓNG ĐÈN" or "SP THỦY TINH"), mapping to the Product Line.
    - `industry_name` (Lớp 1): String (e.g., "Bóng đèn huỳnh quang com-pắc").
    - `default_type` (Loại): String, restricted to `NC` (Nguyên chiếc) or `LK` (Linh kiện). The classification is determined directly by the HS code prefix.
    - `source`: String enum (`system`, `crawled`, `user_input`).
    - `created_at`, `updated_at`.

- **Decision 2: Type and Category Matching by HS Code Prefix**:
  - Instead of guessing component types (`LK`/`NC`) using string keywords, the system resolves the component type (`default_type`) and category (`industry_name`) directly using the longest-match prefix of the HS code present in the `HSTaxonomy` table.

- **Decision 3: Asynchronous Online Crawler**:
  - When an unknown HS code is encountered during dictionary draft generation:
    1. The backend triggers a lookup query using the online crawler (`backend/core/crawler.py`).
    2. The crawler scrapes standard public customs directories or search portals.
    3. If resolved, it extracts the description, sets the default type (NC/LK) based on typical keyword rules, and saves the new record directly to `HSTaxonomy` with `source='crawled'`.

- **Decision 4: Step 1 Manual Intervention Form (Option 1)**:
  - If a file contains HS codes that do not exist in the database and the online crawler fails to resolve them:
    - The wizard halts at Step 1 (generating draft).
    - The frontend displays an interception dialog listing the unresolved HS codes.
    - The user must manually input/confirm the `Dòng sản phẩm`, `Lớp 1`, and `Loại` (NC/LK) for each code.
    - Upon submitting, the frontend calls the backend API to save these definitions, and the draft generation continues seamlessly.

- **Decision 5: Management CRUD & Sidebar**:
  - Add a dedicated page `HSTaxonomy.tsx` linked from the Sidebar. Allows manual editing, adding, and bulk importing of HS taxonomy mappings.

## Risks / Trade-offs

- [Risk] → Crawler might get rate-limited or fail due to network/layout changes.
- [Mitigation] → Manual UI form fallback ensures the user is never blocked.
- [Risk] → Different length HS codes (4, 6, 8, or 10 digits) in raw data.
- [Mitigation] → Implement longest-prefix matching (e.g., matching "85395210" falls back to "853952" -> "8539" if a precise match isn't found).
