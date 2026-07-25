"""
Notification channel backends.

Each backend implements: send(recipient, subject, body, **kwargs) -> bool

Backends are registered in settings and selected by the orchestrator
based on tenant configuration and event channel.
"""
import logging
from abc import ABC, abstractmethod
from django.db import models as db_models

logger = logging.getLogger("healthcare_os.notifications")


class BaseChannelBackend(ABC):
    """Abstract channel backend."""

    @abstractmethod
    def send(self, recipient: str, subject: str, body: str, **kwargs) -> bool:
        """Send notification. Returns True on success, False on failure."""
        ...

    @property
    @abstractmethod
    def channel_name(self) -> str:
        ...


class ConsoleBackend(BaseChannelBackend):
    """Development backend — logs to console instead of sending."""

    channel_name = "console"

    def send(self, recipient: str, subject: str, body: str, **kwargs) -> bool:
        logger.info(
            f"[{self.channel_name.upper()}] TO: {recipient} | "
            f"SUBJECT: {subject} | BODY: {body[:200]}"
        )
        return True


class EmailBackend(BaseChannelBackend):
    """Email channel using Django's email backend."""

    channel_name = "email"

    def send(self, recipient: str, subject: str, body: str, **kwargs) -> bool:
        from django.core.mail import send_mail

        try:
            html_body = kwargs.get("html_body", "")
            send_mail(
                subject=subject,
                message=body,
                from_email=kwargs.get("from_email"),
                recipient_list=[recipient],
                html_message=html_body or None,
                fail_silently=False,
            )
            return True
        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return False


class SMSBackend(BaseChannelBackend):
    """
    SMS channel — provider-agnostic via configuration.

    Supports: Twilio, Vonage, or custom HTTP gateway via settings.
    """

    channel_name = "sms"

    def send(self, recipient: str, subject: str, body: str, **kwargs) -> bool:
        # SMS has no subject — body is the message
        # In production: dispatch to configured provider (Twilio, etc.)
        # For dev: log to console
        logger.info(f"[SMS] TO: {recipient} | BODY: {body[:160]}")
        return True


class WhatsAppBackend(BaseChannelBackend):
    """WhatsApp Business API channel."""

    channel_name = "whatsapp"

    def send(self, recipient: str, subject: str, body: str, **kwargs) -> bool:
        # In production: call WhatsApp Business API
        logger.info(f"[WHATSAPP] TO: {recipient} | BODY: {body[:200]}")
        return True


class NotificationOrchestrator:
    """
    Central notification dispatch service.

    Usage:
        orchestrator = NotificationOrchestrator()
        orchestrator.dispatch(
            tenant=tenant,
            event_type="appointment_reminder",
            channel="email",
            recipient_email="patient@example.com",
            context={"patient_name": "Alice", "appointment_time": "10:30 AM"},
        )
    """

    BACKENDS = {
        "email": EmailBackend(),
        "sms": SMSBackend(),
        "whatsapp": WhatsAppBackend(),
        "console": ConsoleBackend(),
    }

    def dispatch(
        self,
        tenant,
        event_type: str,
        channel: str,
        recipient_email: str = "",
        recipient_phone: str = "",
        recipient_name: str = "",
        recipient_user=None,
        context: dict | None = None,
        template: "NotificationTemplate | None" = None,
    ) -> "NotificationEvent":
        """
        Resolve template, render content, dispatch via channel backend.

        Returns the NotificationEvent record (status = sent or failed).
        """
        import uuid as _uuid
        from django.utils import timezone
        from .models import NotificationEvent, NotificationTemplate

        # Idempotency key
        idempotency_key = _uuid.uuid4().hex

        # Try to find a matching template
        if template is None:
            template = NotificationTemplate.objects.filter(
                event_type=event_type,
                channel=channel,
                is_active=True,
            ).filter(
                db_models.Q(tenant=tenant) | db_models.Q(tenant__isnull=True),
            ).first()

        # Render
        if template and context:
            rendered = template.render(context)
            subject = rendered["subject"]
            body = rendered["body_text"] or rendered["body_html"]
        else:
            subject = event_type.replace("_", " ").title()
            body = str(context) if context else ""

        # Create event record
        event = NotificationEvent.objects.create(
            tenant=tenant,
            template=template,
            event_type=event_type,
            channel=channel,
            recipient_email=recipient_email,
            recipient_phone=recipient_phone,
            recipient_name=recipient_name,
            recipient_user=recipient_user,
            subject=subject,
            body=body,
            status=NotificationEvent.Status.PENDING,
            idempotency_key=idempotency_key,
        )

        # Dispatch
        backend = self.BACKENDS.get(channel, ConsoleBackend())
        recipient = recipient_email if channel == "email" else recipient_phone

        try:
            success = backend.send(
                recipient=recipient,
                subject=subject,
                body=body,
                html_body=rendered.get("body_html", "") if template else "",
            )
            event.status = NotificationEvent.Status.SENT if success else NotificationEvent.Status.FAILED
            event.sent_at = timezone.now() if success else None
        except Exception as e:
            event.status = NotificationEvent.Status.FAILED
            event.error_message = str(e)

        event.save(update_fields=["status", "sent_at", "error_message"])
        return event


# Global orchestrator instance
orchestrator = NotificationOrchestrator()
