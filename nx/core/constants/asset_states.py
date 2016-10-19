OFFLINE  = 0           # Associated file does not exist
ONLINE   = 1           # File exists and is ready to use
CREATING = 2           # File exists, but was changed recently. It is no safe (or possible) to use it yet
TRASHED  = 3           # File has been moved to trash location.
ARCHIVED = 4           # File has been moved to archive location.
RESET    = 5           # Reset metadata action has been invoked. Meta service will update/refresh auto-generated asset information.
