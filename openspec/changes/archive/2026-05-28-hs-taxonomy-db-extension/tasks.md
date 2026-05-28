## 1. Database Implementation

- [x] 1.1 Update the `HSTaxonomy` model in `backend/models.py`.
- [x] 1.2 Include fields: `id`, `hs_code_prefix`, `dong_sp`, `industry_name` (Lớp 1), `default_type` (Loại: NC/LK), `source`, `created_at`, `updated_at`.
- [x] 1.3 Create a database seeding script (`backend/core/seed_taxonomy.py`) that exports existing hardcoded taxonomies (`HS_TAXONOMY`, `DONG_SP_MAP`, `HS_TYPE_MAP`) from `dict_generator.py` into the `HSTaxonomy` table.

## 2. Crawler & API Implementation

- [x] 2.1 Implement the online crawler module in `backend/core/crawler.py` using `httpx`/`BeautifulSoup` to scrape HS descriptions from customs lookup directories.
- [x] 2.2 Create CRUD API endpoints in `backend/main.py`: `GET /api/taxonomy`, `POST /api/taxonomy`, `PUT /api/taxonomy/{id}`, `DELETE /api/taxonomy/{id}`.
- [x] 2.3 Implement `POST /api/taxonomy/check-hs-codes` that accepts raw HS codes, queries the DB (with longest-prefix matching), triggers the crawler for missing ones, and returns a list of unresolved codes.
- [x] 2.4 Implement `POST /api/taxonomy/bulk-save` to save manually inputted HS mappings from the UI.
- [x] 2.5 Implement a bulk CSV/Excel upload endpoint for administrator manual mapping imports.

## 3. Integration with Processing Pipeline

- [x] 3.1 Modify `backend/core/dict_generator.py` to replace hardcoded dictionary lookups with `HSTaxonomy` DB queries.
- [x] 3.2 Ensure the crawler runs automatically inside the pipeline when new/unknown HS codes are encountered.
- [x] 3.3 Ensure the cleaning output file generation references the dynamic DB taxonomy mappings.

## 4. Frontend Implementation

- [x] 4.1 Create the dedicated administration page `src/pages/HSTaxonomy.tsx` with a table view and search, edit, and delete functionality.
- [x] 4.2 Add "HS Taxonomy" route to `App.tsx` and sidebar link in `Sidebar.tsx`.
- [x] 4.3 Update the Dictionary Generator page (Wizard Step 1):
  - Intercept the "Generate Draft" action to call `/api/taxonomy/check-hs-codes`.
  - If unresolved HS codes are returned, display a modal dialog asking the user to manually enter `Dòng sản phẩm` (dropdown), `Lớp 1` (text), and `Loại` (NC/LK radio/select).
  - Submit the form data to `/api/taxonomy/bulk-save` and then proceed automatically to trigger draft generation.

## 5. Verification

- [x] 5.1 Test the online crawler independently with a script.
- [x] 5.2 Test the full CRUD lifecycle and bulk import from the Taxonomy management page.
- [x] 5.3 Test the Wizard Step 1 flow by uploading a raw file with a brand-new HS code, confirming the interception dialog works, saving the mapping, and checking that the database is populated.
- [x] 5.4 Verify that the resulting draft and clean files map the new HS code's product line and type correctly.
