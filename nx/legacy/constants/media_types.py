VIRTUAL = 0
FILE = 1
URI = 2


def get_media_type_id(name):
    return {
        "virtual": VIRTUAL,
        "file": FILE,
        "uri": URI,
    }[name]


def get_media_type_name(id):
    return {
        VIRTUAL: "virtual",
        FILE: "file",
        URI: "uri",
    }[id]
