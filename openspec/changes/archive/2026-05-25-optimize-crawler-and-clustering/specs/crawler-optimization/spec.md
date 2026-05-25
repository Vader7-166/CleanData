## ADDED Requirements

### Requirement: Multi-Level HS Code Crawling
The system SHALL crawl the 4-digit prefix Heading description of an unknown HS code to dynamically resolve the Product Line (`dong_sp`), in addition to crawling the 8-digit detail description for Lớp 1.

#### Scenario: Successful crawling of unknown HS code
- **WHEN** the system checks an unknown HS code like `8539.52.00`
- **THEN** it SHALL crawl both the heading description for `8539` and the full description for `8539.52.00`
- **THEN** it SHALL map the Heading description to `dong_sp` and the full description to `industry_name`

### Requirement: Advanced Text Preprocessing
The system SHALL remove alphanumeric model codes, unit symbols, and dimension strings from the raw product descriptions during text cleaning.

#### Scenario: Text cleaning removes model codes
- **WHEN** cleaning the text `"Bóng Đèn LED RS-378B 15W 12V Philips"`
- **THEN** the cleaned text SHALL be `"Bóng Đèn LED"` (filtering out `RS-378B`, `15W`, `12V`, and optionally `Philips`)

### Requirement: DBSCAN Clustering Tuning
The system SHALL use DBSCAN clustering with `eps=0.70` and `min_samples=8` to perform product grouping.

#### Scenario: Clustering groups products
- **WHEN** vectorizing and clustering raw products using the updated DBSCAN parameters
- **THEN** the system SHALL produce fewer small clusters and classify minor noisy groups as outliers (`-1`)
