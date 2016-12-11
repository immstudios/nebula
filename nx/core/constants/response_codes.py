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

DEFAULT_RESPONSE_MESSAGES = {
        200 : "OK",
        201 : "created",
        202 : "accepted",
        204 : "no content",
        206 : "partial",

        400 : "bad request",
        401 : "unauthorised",
        404 : "not found",

        500 : "internal",
        503 : "not implemented",
        504 : "timeout",
        503 : "service unavailable"
    }
