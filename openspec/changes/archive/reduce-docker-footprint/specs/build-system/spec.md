## ADDED Requirements

### Requirement: Minimal Build Context
The build context for both backend and frontend SHALL NOT include local development artifacts or large datasets.

#### Scenario: Verify .dockerignore exists
- **WHEN** building the docker image
- **THEN** `.venv` and `node_modules` SHALL NOT be copied to the docker daemon

### Requirement: Optimized Backend Image
The backend image SHALL be optimized for size by removing build-time dependencies after use.

#### Scenario: Check image size
- **WHEN** the backend image is built
- **THEN** it SHALL NOT contain `build-essential` or cached pip packages
