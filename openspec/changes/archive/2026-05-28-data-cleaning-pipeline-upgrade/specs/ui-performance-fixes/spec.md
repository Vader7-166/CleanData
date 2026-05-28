## ADDED Requirements

### Requirement: Optimized Batch Preview API Fetching
The frontend dashboard SHALL fetch preview data for completed files in a batch concurrently rather than sequentially.

#### Scenario: Viewing a Large Batch Preview
- **WHEN** a user opens the Batch Preview dialog for a batch containing dozens of files
- **THEN** the frontend retrieves the preview data for all files concurrently using `Promise.all()` (or a single backend API call), significantly reducing loading time.

### Requirement: Robust Chart Rendering
The Batch Preview dashboard charts SHALL render without overlapping or clipping text when displaying long dataset labels.

#### Scenario: Displaying Long Product/Company Names
- **WHEN** the dashboard renders the PieChart or BarChart with extremely long text labels
- **THEN** it applies text truncation (e.g., ellipses), custom tooltips, and appropriate layout margins to ensure the interface remains visually intact.

### Requirement: Robust Table Rendering
The Batch Preview data table SHALL correctly display all columns and keys across the dataset regardless of null values in the first row.

#### Scenario: Rendering Inconsistent Schema Rows
- **WHEN** the preview dataset contains rows with missing or extra columns compared to the first row
- **THEN** the table extracts all unique column keys across the entire dataset to render headers, preventing hidden columns, and utilizes unique row keys in the React DOM.
