## Why

To provide better data insights and categorization, the system needs to associate HS codes with specific industry taxonomies (HS_TAXONOMY). This extension allows for industry-level reporting and more accurate filtering of processed data.

## What Changes

- **Schema Update**: Add industry/taxonomy fields to the database tables that store HS code information.
- **Model Modification**: Update SQLAlchemy/Pydantic models in the backend to include the new taxonomy attributes.
- **HS Taxonomy Management Page**: Create a new frontend page with a table-based interface to list, add, edit, and delete HS code to industry mappings.
- **CRUD APIs**: Implement backend endpoints to support all CRUD operations for the HS taxonomy data.
- **Data Migration**: (If necessary) Provide a way to populate the new taxonomy fields from existing HS code mappings.

## Capabilities

### New Capabilities
- `hs-taxonomy-management-page`: A dedicated interface for administrators to manage the global HS code to industry mapping table.

### Modified Capabilities
- `database-schema-core`: Extend the existing core schema to support HS code to industry/taxonomy mappings.

## Impact

- Database: Schema changes (adding columns or new mapping tables).
- Backend: `backend/models.py`, `backend/database.py`.
- Data Processing: `backend/core/dictionary_matcher.py` might be updated to leverage these taxonomies.
