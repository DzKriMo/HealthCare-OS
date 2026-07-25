"""
Custom exception handling for DRF.
"""
import uuid
import logging

from rest_framework.views import exception_handler
from rest_framework.response import Response

logger = logging.getLogger("healthcare_os")


def custom_exception_handler(exc, context):
    """
    Wrap DRF exceptions with correlation IDs and structured error format.
    """
    response = exception_handler(exc, context)

    if response is not None:
        correlation_id = str(uuid.uuid4())
        request = context.get("request")

        response.data = {
            "error": {
                "type": type(exc).__name__,
                "detail": response.data,
                "correlation_id": correlation_id,
            }
        }

        logger.error(
            "API error",
            extra={
                "correlation_id": correlation_id,
                "status_code": response.status_code,
                "path": request.path if request else "",
                "method": request.method if request else "",
            },
        )

        response["X-Correlation-ID"] = correlation_id

    return response
