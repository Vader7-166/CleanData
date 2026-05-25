## Context

Currently, the system uses dictionaries for data cleaning, but there is no centralized database table that maps HS codes to industry taxonomies (HS_TAXONOMY). Adding this mapping to the database allows for automated categorization and enhanced reporting.

## Goals / Non-Goals

**Goals:**
- Create a persistent mapping between HS code prefixes and industry categories.
- Provide an API to query and manage these mappings.
- Use these mappings to enrich processed data results.

**Non-Goals:**
- Automatically generating the taxonomy data (it must be provided or imported).
- Replacing the existing dictionary-based matching logic.

## Decisions

- **Decision 1: New Reference Table**: Create an `HSTaxonomy` table.
  - Columns: `id`, `hs_code_prefix` (String, e.g., "7020"), `industry_name` (String, e.g., "Glassware"), `description` (String), `created_at`.
- **Decision 2: Prefix Matching**: Matching will be done using the prefix of the HS code. A 4-digit prefix is usually sufficient for high-level industry classification.
- **Decision 3: Dictionary Integration**: When a dictionary is used, the system can cross-reference the HS code in the dictionary with the `HSTaxonomy` table to add industry labels to the output.
- **Decision 4: Table-based CRUD UI**: Use a responsive data table (e.g., using Tailwind and a local state or SWR) to display mappings. Implement modals or inline forms for adding and editing records.
- **Decision 5: Sidebar Integration**: Add a new link to the sidebar specifically for "HS Taxonomy Management" to ensure easy access.

## Risks / Trade-offs

- [Risk] → Different HS code versions (e.g., 2017 vs 2022) might have slight variations.
- [Mitigation] → Focus on stable 4-digit prefixes or provide versioning in the taxonomy table.
- [Risk] → Maintaining the taxonomy data could be a manual burden.
- [Mitigation] → Provide a bulk import feature (CSV/Excel) for the taxonomy table.
