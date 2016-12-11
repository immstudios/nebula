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

def get_content_type_id(name):
    return {
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
	}[name]


def get_content_type_name(id):
    return {
            AUDIO : "audio",
            VIDEO : "video",
            IMAGE : "image",
            TEXT  : "text",
            DATABROADCASTING : "databroadcasting",
            INTERSTITIAL : "interstitial",
            EDUCATION : "education",
            APPLICATION : "application",
            GAME : "game",
            PACKAGE : "package"
	}[id]
