from nx import NebulaResponse

from nebulacore.constants import (
    ERROR_UNAUTHORISED,
    ERROR_NOT_IMPLEMENTED
)

__all__ = ["api_message"]


def api_message(**kwargs):
    if not kwargs.get("user", None):
        return NebulaResponse(ERROR_UNAUTHORISED)

    return NebulaResponse(ERROR_NOT_IMPLEMENTED)
