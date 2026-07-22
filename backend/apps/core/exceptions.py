import traceback

from django.conf import settings
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler


def custom_exception_handler(exc, context):
    """
    Normalize DRF errors to {detail, status_code}.
    Also convert unhandled exceptions into JSON so the SPA never only sees HTML 500.
    """
    response = exception_handler(exc, context)
    if response is not None:
        data = response.data
        # Field-error dict → keep as detail object for the SPA formatter
        if isinstance(data, dict) and "detail" in data and len(data) == 1:
            payload = {
                "detail": data["detail"],
                "status_code": response.status_code,
            }
        elif isinstance(data, dict) and "detail" not in data:
            # {"title": ["..."], "assignee_id": ["..."]}
            payload = {"detail": data, "status_code": response.status_code}
        else:
            payload = {
                "detail": data.get("detail", data) if isinstance(data, dict) else data,
                "status_code": response.status_code,
            }
        response.data = payload
        return response

    # Unhandled (IntegrityError, ValueError, etc.)
    traceback.print_exc()
    detail = str(exc) or exc.__class__.__name__
    if not settings.DEBUG:
        detail = "Internal server error. Please try again."
    return Response(
        {"detail": detail, "status_code": 500},
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
