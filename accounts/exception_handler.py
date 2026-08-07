from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_default_exception_handler
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Wraps DRF's default exception handler so every kind of bad request -
    missing/invalid auth, invalid or missing fields, hitting a URL that
    doesn't exist, or an unexpected server-side error - always comes back
    as the same predictable JSON shape:

        {"error": "<human readable message>"}
        {"error": "Invalid request.", "details": {"quantity": ["..."]}}

    instead of Django's HTML debug page, a bare stack trace, or DRF's
    default (sometimes {"detail": ...}, sometimes a raw list/dict
    depending on exception type) - so nothing that reaches a client ever
    leaks internal error detail, regardless of what "broken" input caused it.
    """
    response = drf_default_exception_handler(exc, context)

    if response is None:
        # Not something DRF recognizes (e.g. a database error, an
        # unhandled bug). Don't leak internals to the client.
        return Response(
            {"error": "Something went wrong processing that request."},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

    data = response.data

    if isinstance(data, dict) and set(data.keys()) == {'detail'}:
        # NotAuthenticated / AuthenticationFailed / PermissionDenied /
        # NotFound / MethodNotAllowed / Throttled all land here.
        response.data = {"error": str(data['detail'])}
    else:
        # Serializer validation errors - a dict keyed by field name (or a
        # list, for non_field_errors) - get wrapped consistently too.
        response.data = {"error": "Invalid request.", "details": data}

    return response
