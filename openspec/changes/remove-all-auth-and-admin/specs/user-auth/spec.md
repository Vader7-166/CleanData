## REMOVED Requirements

### Requirement: User Authentication
The system used to require users to provide a username and password before uploading files.
**Reason**: Project requirement to make the tool fully anonymous.
**Migration**: Simply remove auth-related code and use the `/upload` endpoint directly.

### Requirement: Admin Access
The system used to provide a default `admin` user for moderation.
**Reason**: Admin/User moderation features are being completely removed.
**Migration**: Remove all `admin` initialization logic and user model.
