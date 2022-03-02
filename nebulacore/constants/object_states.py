OFFLINE = 0  # Associated file does not exist
ONLINE = 1  # File exists and is ready to use
CREATING = 2  # File exists, but was changed recently. It is no safe (or possible) to use it yet
TRASHED = 3  # File has been moved to trash location.
ARCHIVED = 4  # File has been moved to archive location.
RESET = 5  # Reset metadata action has been invoked. Meta service will update/refresh auto-generated asset information.
CORRUPTED = 6
REMOTE = 7
UNKNOWN = 8
AIRED = 9  # Auxiliary value.
ONAIR = 10
RETRIEVING = 11


def get_object_state_id(name):
    return {
        "offline": OFFLINE,
        "online": ONLINE,
        "creating": CREATING,
        "trashed": TRASHED,
        "archived": ARCHIVED,
        "reset": RESET,
        "corrupted": CORRUPTED,
        "remote": REMOTE,
        "unknown": UNKNOWN,
        "aired": AIRED,
        "onair": ONAIR,
        "retrieving": RETRIEVING,
    }[name]


def get_object_state_name(id):
    return {
        OFFLINE: "offline",
        ONLINE: "online",
        CREATING: "creating",
        TRASHED: "trashed",
        ARCHIVED: "archived",
        RESET: "reset",
        CORRUPTED: "corrupted",
        REMOTE: "remote",
        UNKNOWN: "unknown",
        AIRED: "aired",
        ONAIR: "onair",
        RETRIEVING: "retrieving",
    }[id]
