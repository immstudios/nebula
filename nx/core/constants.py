#!/usr/bin/env python
# -*- coding: utf-8 -*-

########################################################################
## Constants

# service states
STOPPED  = 0           # Service is stopped. Surprisingly.
STARTED  = 1           # Service is started and running
STARTING = 2           # Service start requested.
STOPPING = 3           # Service graceful stop requested. It should shutdown itself after current iteration
KILL     = 4           # Service force stop requested. Dispatch is about to kill -9 it


ASSET = 0
ITEM  = 1
BIN   = 2
EVENT = 3
USER  = 4 

OBJECT_TYPES = {
 "asset"  : 0,
 "item"   : 1,
 "bin"    : 2,
 "event"  : 3,
 "user"   : 4
 }


# content_type
TEXT     = 0
VIDEO    = 1
AUDIO    = 2
IMAGE    = 3

CONTENT_TYPES = {
    "TEXT"  : TEXT,
    "VIDEO" : VIDEO,
    "AUDIO" : AUDIO,
    "IMAGE" : IMAGE
}

# media_type
FILE     = 0           # There is (or should be) physical file specified by 'storage' and 'path' metadata
VIRTUAL  = 1           # Asset exists only as DB record (macro, text...)

# asset status
OFFLINE  = 0           # Associated file does not exist
ONLINE   = 1           # File exists and is ready to use
CREATING = 2           # File exists, but was changed recently. It is no safe (or possible) to use it yet
TRASHED  = 3           # File has been moved to trash location.
ARCHIVED = 4           # File has been moved to archive location.
RESET    = -1          # Reset metadata action has been invoked. Meta service will update/refresh auto-generated asset information.

# meta_classes
TEXT         = 0       # Single-line plain text (default)
BLOB         = 1       # Multiline text. 'syntax' can be provided in config
INTEGER      = 2       # Integer only value (for db keys etc)
NUMERIC      = 3       # Any integer of float number. 'min', 'max' and 'step' values can be provided in config
BOOLEAN      = 4       # 1/0 checkbox
DATETIME     = 5       # Date and time information. Stored as timestamp
TIMECODE     = 6       # Timecode information, stored as float(seconds), presented as HH:MM:SS:FF or HH:MM:SS.CS (centiseconds)
REGIONS      = 7
FRACTION     = 8       # 16/9 etc...
SELECT       = 9       # Select box ops stored as {'value':'title', 'another_value':'another title'}
CS_SELECT    = 10      
ENUM         = 11      # Similar to select - for integer values
CS_ENUM      = 12

# storage types

LOCAL    = 0
CIFS     = 1
NFS      = 2
FTP      = 3

# Job status (stored in nx_jobs/progress)

PENDING   = -1
COMPLETED = -2
FAILED    = -3
ABORTED   = -4

# Channel types

PLAYOUT   = 0
INGEST    = 1
CAMPAIGN  = 2

#################################################
## Log levels

DEBUG       = 0
INFO        = 1
WARNING     = 2
ERROR       = 3
GOOD_NEWS   = 4

## Log level
#################################################
## Block playback modes

RUN_AUTO    = 0    # First item of this block is cued right after last item of previous block
RUN_MANUAL  = 1    # Playback stops at the end of the last item of previous block
RUN_SOFT    = 2    # First item of this block is cued if previous block is running and current_time >= scheduled_time
RUN_HARD    = 3    # First item of this block starts immediately if previous block is running and current_time >= scheduled_time

## Block playback modes
#################################################
## Hive / Play response codes

SUCCESS_OK                = 200
SUCCESS_CREATED           = 201
SUCCESS_ACCEPTED          = 202
SUCCESS_NOCONTENT         = 204
SUCCESS_PARTIAL           = 206

ERROR_BAD_REQUEST         = 400
ERROR_UNAUTHORISED        = 401
ERROR_NOT_FOUND           = 404

ERROR_INTERNAL            = 500
ERROR_NOT_IMPLEMENTED     = 503
ERROR_TIMEOUT             = 504
ERROR_SERVICE_UNAVAILABLE = 503

