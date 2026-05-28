## ADDED Requirements

### Requirement: List Uploaded Dictionaries
The system SHALL display a list of all uploaded dictionaries in the user interface.

#### Scenario: Display Dictionary List
- **WHEN** a user navigates to the dictionary management page
- **THEN** the system SHALL fetch and display a list containing the names and upload dates of all stored dictionaries.

### Requirement: Active Dictionary Selection
The system SHALL allow the user to select one dictionary as the "active" dictionary for the data cleaning pipeline.

#### Scenario: Select Active Dictionary
- **WHEN** a user selects a specific dictionary from the list and confirms the selection
- **THEN** the system SHALL mark that dictionary as active and apply it to all subsequent product classification tasks.

### Requirement: Dictionary Deletion
The system SHALL allow users to delete uploaded dictionaries.

#### Scenario: Delete a Dictionary
- **WHEN** a user chooses to delete a dictionary from the list
- **THEN** the system SHALL remove the file from storage and its metadata from the database.
