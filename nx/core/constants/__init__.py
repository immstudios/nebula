from asset_states import *
from channel_types import *
from job_states import *
from media_types import *
from response_codes import *
from run_modes import *
from service_states import *
from storage_types import *

# ContentTypeCS
# urn:tva:metadata-cs:ContentTypeCS
# versionDate="2013-01-07"
# This is a set of terms used to indicate what kinds of content are
# used as main Program or used in Package
# Content can be classified by either the type of content or the subject of content

AUDIO = 1
VIDEO = 2
IMAGE = 3
TEXT = 4
DATABROADCASTING = 5
INTERSTITIAL = 6
EDUCATION = 7
APPLICATION = 8
GAME = 9
PACKAGE = 10

CONTENT_TYPES = {
    "audio" : AUDIO,
    "video" : VIDEO,
    "stillimage" : IMAGE,
    "text"  : TEXT,
    "databroadcasting" : DATABROADCASTING,
    "interstitial" : INTERSTITIAL,
    "education" : EDUCATION,
    "application" : APPLICATION,
    "game" : GAME,
    "package" : PACKAGE
}

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

