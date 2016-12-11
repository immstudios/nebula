ASSET = 0
ITEM = 1
BIN = 2
EVENT = 3
USER = 4

def get_object_type_id(name):
    return {
            "asset" : ASSET,
            "item" : ITEM,
            "bin" : BIN,
            "event" : EVENT,
            "user" : USER
        }[name.lower()]

def get_object_type_name(id):
    return {
            ASSET : "asset",
            ITEM : "item",
            BIN : "bin",
            EVENT : "event",
            USER : "user"
        }[id]