"""Return system settings."""

from nx import NebulaResponse, config, storages
from nebulacore.constants import ERROR_UNAUTHORISED

__all__ = ["api_settings"]


def api_settings(**kwargs):
    """Return system settings."""
    if not kwargs.get("user", None):
        return NebulaResponse(ERROR_UNAUTHORISED)
    data = {}
    for key in [
            "actions",
            "cs",
            "folders",
            "ingest_channels",
            "meta_types",
            "playout_channels",
            "proxy_url",
            "services",
            "seismic_addr",
            "seismic_port",
            "site_name",
            "views",
            "language"
            ]:
        if key in config:
            data[key] = config[key]

    data["storages"] = {}
    for k in config["storages"]:
        data["storages"][k] = {"title": storages[k].title}
    return NebulaResponse(200, data=data)
