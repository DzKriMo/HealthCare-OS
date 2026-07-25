"""
Audit middleware — captures request metadata and provides audit context.

Full implementation for Sprint 6:
    - Generates correlation_id for every request.
    - Captures IP, user agent, actor.
    - Provides utility to record audit events throughout the app.
"""
import uuid
import json
import logging
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger("healthcare_os.audit")


class AuditMiddleware(MiddlewareMixin):
    """
    Attach correlation_id and audit context to every request.

    The correlation_id flows through the entire request lifecycle and
    is included in API error responses, logs, and audit events.
    """

    def process_request(self, request):
        # Generate correlation ID
        correlation_id = request.META.get("HTTP_X_CORRELATION_ID", str(uuid.uuid4()))
        request.correlation_id = correlation_id

        # Capture audit metadata
        request.audit_meta = {
            "correlation_id": correlation_id,
            "ip_address": self._get_client_ip(request),
            "user_agent": request.META.get("HTTP_USER_AGENT", ""),
            "session_id": None,
        }

        # Attach correlation ID to response later
        request._correlation_id = correlation_id

    def process_response(self, request, response):
        """Attach correlation ID to response headers."""
        if hasattr(request, "_correlation_id"):
            response["X-Correlation-ID"] = request._correlation_id
        return response

    def _get_client_ip(self, request) -> str | None:
        xff = request.META.get("HTTP_X_FORWARDED_FOR")
        if xff:
            return xff.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR")


class AuditService:
    """
    Service for recording audit events from anywhere in the app.

    Usage:
        AuditService.record(
            tenant=request.tenant,
            actor=request.user,
            entity_type="Patient",
            entity_id=str(patient.id),
            action="update",
            before_value={"name": "Old"},
            after_value={"name": "New"},
        )
    """

    @staticmethod
    def record(
        tenant=None,
        actor=None,
        entity_type: str = "",
        entity_id: str = "",
        entity_display: str = "",
        action: str = "",
        before_value: dict | None = None,
        after_value: dict | None = None,
        correlation_id: str | None = None,
        session_id: str | None = None,
        ip_address: str | None = None,
        user_agent: str = "",
        is_sensitive: bool = False,
        extra: dict | None = None,
    ):
        """Record an audit event. Fire-and-forget — never blocks the request."""
        from .models import AuditEvent

        try:
            kwargs = {
                "tenant": tenant,
                "actor": actor,
                "actor_display": str(actor) if actor else "",
                "entity_type": entity_type,
                "entity_id": entity_id,
                "entity_display": entity_display,
                "action": action,
                "before_value": before_value,
                "after_value": after_value,
                "correlation_id": correlation_id or str(uuid.uuid4()),
                "ip_address": ip_address or "",
                "user_agent": user_agent,
                "is_sensitive": is_sensitive,
                "extra": extra or {},
            }
            # Only add session_id if it has a value (avoid passing None)
            if session_id:
                kwargs["session_id"] = session_id
            AuditEvent.objects.create(**kwargs)
        except Exception as e:
            # Audit failure should NEVER break the main request
            logger.error(f"Failed to record audit event: {e}", exc_info=True)

    @staticmethod
    def record_from_request(
        request,
        entity_type: str = "",
        entity_id: str = "",
        entity_display: str = "",
        action: str = "",
        before_value: dict | None = None,
        after_value: dict | None = None,
        is_sensitive: bool = False,
    ):
        """Convenience method using request context."""
        meta = getattr(request, "audit_meta", {})
        AuditService.record(
            tenant=getattr(request, "tenant", None),
            actor=request.user if request.user.is_authenticated else None,
            entity_type=entity_type,
            entity_id=entity_id,
            entity_display=entity_display,
            action=action,
            before_value=before_value,
            after_value=after_value,
            correlation_id=getattr(request, "correlation_id", str(uuid.uuid4())),
            ip_address=meta.get("ip_address"),
            user_agent=meta.get("user_agent", ""),
            is_sensitive=is_sensitive,
        )
