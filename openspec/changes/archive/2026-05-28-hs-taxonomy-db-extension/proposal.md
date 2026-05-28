## Why

To provide better data insights and categorization, the system needs to associate HS codes with specific industry taxonomies, product lines, and component type mappings dynamically. Moving this from hardcoded dictionaries in Python to the database and integrating a lookup crawler will make the dictionary generation and data cleaning pipeline completely dynamic.

## What Changes

- **Schema Update**: Create `HSTaxonomy` table storing HS code prefixes mapped to `Dòng SP` (Product Line), `Lớp 1` (Industry Name), `Loại` (NC/LK), and metadata like `source` (system, crawled, user_input).
- **Online HS Crawler**: Implement an asynchronous module to crawl and lookup descriptions of new HS codes from public customs/tax directories, automatically predicting default types and saving to the DB.
- **Manual Intervention UI**: Integrate an interception step in the Dictionary Generator Wizard (Step 1) that prompts the user to input details (Dòng sản phẩm, Lớp 1, Loại) for any unknown HS codes that the crawler fails to resolve.
- **HS Taxonomy Management Page**: Create a dedicated management interface to view, add, edit, and bulk-import/export HS taxonomy records.
- **CRUD APIs**: Implement backend endpoints for taxonomy lookup, creation, and crawler queries.

## Capabilities

### New Capabilities
- `hs-taxonomy-management-page`: A dedicated interface to manage the global HS code to taxonomy mapping table.
- `hs-taxonomy-crawler-lookup`: Asynchronous online search and crawl capability for unknown HS codes.

### Modified Capabilities
- `database-schema-core`: Extend the database schema to support the complete `HSTaxonomy` definition (including Dòng SP and Loại).
- `dictionary-generator-wizard`: Update the draft generation wizard to query the database, invoke the crawler, and prompt the user on unknown HS codes.

## Impact

- Database: New `HSTaxonomy` table.
- Backend: `backend/models.py`, `backend/core/crawler.py` (new), `backend/core/dict_generator.py`.
- Frontend: `src/pages/HSTaxonomy.tsx`, `src/pages/DictWizard.tsx` (or dictionary generator page).
