SUCCESS_OK = 200
SUCCESS_CREATED = 201
SUCCESS_ACCEPTED = 202
SUCCESS_NOCONTENT = 204
SUCCESS_PARTIAL = 206

ERROR_BAD_REQUEST = 400
ERROR_UNAUTHORISED = 401
ERROR_ACCESS_DENIED = 403
ERROR_NOT_FOUND = 404
ERROR_LOCKED = 423

ERROR_INTERNAL = 500
ERROR_BAD_GATEWAY = 502
ERROR_NOT_IMPLEMENTED = 503
ERROR_TIMEOUT = 504
ERROR_SERVICE_UNAVAILABLE = 503

DEFAULT_RESPONSE_MESSAGES = {
    200: "OK",
    201: "Created",
    202: "Accepted",
    204: "No content",
    206: "Partial content",
    400: "Bad request",
    401: "Unauthorised",
    403: "Access denied",
    404: "Not found",
    423: "Locked",
    500: "Internal server error",
    502: "Bad gateway",
    503: "Not implemented",
    504: "Timeout",
    503: "Service unavailable",
}
