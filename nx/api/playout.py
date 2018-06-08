import requests

from nx import *

__all__ = ["api_playout"]

def api_playout(**kwargs):
    if not kwargs.get("user", None):
        return {'response' : 401, 'message' : 'unauthorized'}
    user = User(meta=kwargs["user"])
    #TODO: ACL HERE

    action = kwargs.get("action", False)
    id_channel = int(kwargs.get("id_channel", False))

    if not action in ["cue", "take", "abort", "freeze", "retake", "plugin_list", "plugin_exec", "stat", "recover"]:
        return {'response' : 400, 'message' : 'Unsupported action {}'.format(action)}
    if not id_channel in config["playout_channels"]:
        return {'response' : 400, 'message' : 'Unknown channel {}'.format(id_channel)}

    channel_config = config["playout_channels"][id_channel]

    controller_url = "http://{}:{}".format(
            channel_config.get("controller_host", "localhost"),
            channel_config.get("controller_port", 42100)
        )
    response = requests.post(controller_url + "/" + action, data=kwargs)

    rdata = json.loads(response.text)
    return rdata




