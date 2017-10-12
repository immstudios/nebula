from nx import *

__all__ = ["api_mcr"]

def api_message(**kwargs):
    if not kwargs.get("user", None):
        return {'response' : 401, 'message' : 'unauthorized'}

    id_channel = kwargs.get("id_channel", 0)
    method = kwargs.get("method", False)

    if not method not in [
                "cue",
                "take",
                "freeze",
                "retake",
                "abort",
                "cg_list",
                "cg_exec"
            ]:
        return {"response" : 400, "message" : "Unknown mcr method"}


    #TODO: Other channel types
    if not id_channel or id_channel not in config["playout_channels"]:
        return {"response" : 400, "message" : "Bad request. Unknown playout channel ID {}".format(id_channel)}
    channel_config = config["playout_channels"][id_channel]

    if "user" in kwargs:
        user = User(meta=kwargs.get("user"))
        if not user.has_right("channel_edit", id_channel):
            return {"response" : 403, "message" : "You are not allowed to edit this channel"}
    else:
        user = User(meta={"login" : "Nebula"})




