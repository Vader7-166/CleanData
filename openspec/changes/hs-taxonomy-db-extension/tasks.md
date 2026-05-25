## 1. Database Implementation

- [ ] 1.1 Create the `HSTaxonomy` model in `backend/models.py`.
- [ ] 1.2 Add fields: `id`, `hs_code_prefix`, `industry_name`, `description`, `created_at`.
- [ ] 1.3 Update the database schema (migration or manual table creation).

## 2. API Implementation

- [ ] 2.1 Create CRUD API endpoints in `backend/main.py`: `GET /api/taxonomy`, `POST /api/taxonomy`, `PUT /api/taxonomy/{id}`, `DELETE /api/taxonomy/{id}`.
- [ ] 2.2 Implement a bulk upload endpoint for HS Taxonomy (CSV/Excel).

## 3. Frontend Implementation

- [ ] 3.1 Create a new page component `src/pages/HSTaxonomy.tsx`.
- [ ] 3.2 Implement a data table to list all HS Taxonomy mappings.
- [ ] 3.3 Create a modal or form component for Adding and Editing mappings.
- [ ] 3.4 Implement Delete confirmation logic.
- [ ] 3.5 Add "HS Taxonomy" link to the `Sidebar.tsx` and configure the route in `App.tsx`.

## 4. Integration with Processing Pipeline

- [ ] 4.1 Update the `Dictionary` model or `ProcessingJob` result logic to include industry information from the taxonomy table.
- [ ] 4.2 Ensure the output file generation includes the `Industry` column if a match is found.

## 5. Verification

- [ ] 5.1 Test the full CRUD lifecycle from the UI.
- [ ] 5.2 Import a sample HS Taxonomy dataset and verify it appears in the table.
- [ ] 5.3 Process a file and verify that the industry names appear correctly in exported files.
