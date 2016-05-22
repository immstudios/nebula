from .content_types import *
from .response_codes import *

#
# service states
#

STOPPED  = 0           # Service is stopped. Surprisingly.
STARTED  = 1           # Service is started and running
STARTING = 2           # Service start requested.
STOPPING = 3           # Service graceful stop requested. It should shutdown itself after current iteration
KILL     = 4           # Service force stop requested. Dispatch is about to kill -9 it

#
# media types
#

VIRTUAL = 0
FILE = 1
URL = 2

#
# asset status
#

OFFLINE  = 0           # Associated file does not exist
ONLINE   = 1           # File exists and is ready to use
CREATING = 2           # File exists, but was changed recently. It is no safe (or possible) to use it yet
TRASHED  = 3           # File has been moved to trash location.
ARCHIVED = 4           # File has been moved to archive location.
RESET    = 5           # Reset metadata action has been invoked. Meta service will update/refresh auto-generated asset information.

#
# meta_classes
#

STRING       = 0       # Single-line plain text (default)
TEXT         = 1       # Multiline text. 'syntax' can be provided in config
INTEGER      = 2       # Integer only value (for db keys etc)
NUMERIC      = 3       # Any integer of float number. 'min', 'max' and 'step' values can be provided in config
BOOLEAN      = 4       # 1/0 checkbox
DATETIME     = 5       # Date and time information. Stored as timestamp
TIMECODE     = 6       # Timecode information, stored as float(seconds), presented as HH:MM:SS:FF or HH:MM:SS.CS (centiseconds)
REGIONS      = 7
FRACTION     = 8       # 16/9 etc...
SELECT       = 9
LIST         = 10

#
# Job status (stored in nx_jobs/progress)
#

PENDING   = -1
COMPLETED = -2
FAILED    = -3
ABORTED   = -4

#
# Channel types
#

PLAYOUT   = 0
INGEST    = 1
CAMPAIGN  = 2

#
# Block playback modes
#

RUN_AUTO    = 0    # First item of this block is cued right after last item of previous block
RUN_MANUAL  = 1    # Playback stops at the end of the last item of previous block
RUN_SOFT    = 2    # First item of this block is cued if previous block is running and current_time >= scheduled_time
RUN_HARD    = 3    # First item of this block starts immediately if previous block is running and current_time >= scheduled_time
