"""
Notification models — Sprint 5.

Template engine with per-tenant overrides, multi-channel dispatch
(Email, SMS, WhatsApp, Push), delivery tracking.
"""
import uuid
from django.db import models
from tenancy.models import Tenant
from tenancy.managers import TenantScopedManager


class NotificationTemplate(models.Model):
    """
    Notification template with multi-language and per-tenant support.

    Templates use Jinja2-style variables: {{ patient_name }}, {{ appointment_time }}, etc.
    """

    class Channel(models.TextChoices):
        EMAIL = "email", "Email"
        SMS = "sms", "SMS"
        WHATSAPP = "whatsapp", "WhatsApp"
        PUSH = "push", "Push Notification"

    class EventType(models.TextChoices):
        APPOINTMENT_SCHEDULED = "appointment_scheduled", "Appointment Scheduled"
        APPOINTMENT_REMINDER = "appointment_reminder", "Appointment Reminder"
        APPOINTMENT_CANCELLED = "appointment_cancelled", "Appointment Cancelled"
        MISSED_APPOINTMENT = "missed_appointment", "Missed Appointment"
        INVOICE_ISSUED = "invoice_issued", "Invoice Issued"
        PAYMENT_RECEIVED = "payment_received", "Payment Received"
        PAYMENT_OVERDUE = "payment_overdue", "Payment Overdue"
        RESULT_READY = "result_ready", "Lab Result Ready"
        FOLLOW_UP_DUE = "follow_up_due", "Follow-Up Due"
        PRESCRIPTION_READY = "prescription_ready", "Prescription Ready"
        STOCK_BELOW_THRESHOLD = "stock_below_threshold", "Stock Below Threshold"
        CUSTOM = "custom", "Custom"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="notification_templates",
        null=True, blank=True,
        help_text="Null for system-wide default templates.",
    )
    name = models.CharField(max_length=200)
    event_type = models.CharField(max_length=50, choices=EventType.choices, default=EventType.CUSTOM)
    channel = models.CharField(max_length=20, choices=Channel.choices)

    # Template content
    subject = models.CharField(max_length=300, blank=True, help_text="Email subject line.")
    body_text = models.TextField(blank=True, help_text="Plain text version.")
    body_html = models.TextField(blank=True, help_text="HTML version (email/WhatsApp).")

    # Variables available in this template (documentation)
    available_variables = models.JSONField(
        default=list,
        help_text='List of variable names: ["patient_name", "appointment_time", ...]',
    )

    language = models.CharField(max_length=10, default="en")

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "notifications_template"
        ordering = ["event_type", "channel"]
        constraints = [
            models.UniqueConstraint(
                fields=["tenant", "event_type", "channel", "language"],
                name="unique_template_per_tenant_event_channel_lang",
            ),
        ]

    def __str__(self):
        return f"{self.name} ({self.event_type}/{self.channel})"

    def render(self, context: dict) -> dict:
        """Render template with context variables. Returns {subject, body_text, body_html}."""
        import re

        def replace_vars(text: str) -> str:
            if not text:
                return text
            for key, value in context.items():
                text = text.replace("{{ " + key + " }}", str(value))
                text = text.replace("{{" + key + "}}", str(value))
            return text

        return {
            "subject": replace_vars(self.subject),
            "body_text": replace_vars(self.body_text),
            "body_html": replace_vars(self.body_html),
        }


class NotificationEvent(models.Model):
    """
    A fired notification — records the dispatch attempt and delivery status.

    Created by the notification orchestrator when a domain event triggers
    a notification rule.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        SENT = "sent", "Sent"
        DELIVERED = "delivered", "Delivered"
        FAILED = "failed", "Failed"
        BOUNCED = "bounced", "Bounced"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="notification_events")
    template = models.ForeignKey(
        NotificationTemplate, on_delete=models.PROTECT, null=True, blank=True,
    )

    event_type = models.CharField(max_length=50, choices=NotificationTemplate.EventType.choices)
    channel = models.CharField(max_length=20, choices=NotificationTemplate.Channel.choices)

    # Recipient
    recipient_email = models.EmailField(blank=True)
    recipient_phone = models.CharField(max_length=30, blank=True)
    recipient_name = models.CharField(max_length=200, blank=True)
    recipient_user = models.ForeignKey(
        "identity.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="notifications",
    )

    # Rendered content (snapshotted at send time)
    subject = models.CharField(max_length=500, blank=True)
    body = models.TextField(blank=True)

    # Status
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True)

    # Tracking
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    # Idempotency
    idempotency_key = models.CharField(max_length=100, unique=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "notifications_event"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant"]),
            models.Index(fields=["tenant", "event_type"]),
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["recipient_user"]),
        ]

    def __str__(self):
        return f"{self.event_type}/{self.channel} → {self.recipient_name} [{self.status}]"


class NotificationChannelConfig(models.Model):
    """
    Per-tenant channel configuration — enabled/disabled, credentials, rate limits.
    """

    tenant = models.OneToOneField(
        Tenant, on_delete=models.CASCADE, related_name="notification_config",
    )
    email_enabled = models.BooleanField(default=True)
    email_provider = models.CharField(max_length=50, default="smtp")
    email_from_address = models.EmailField(default="noreply@healthcare-os.com")
    email_from_name = models.CharField(max_length=100, default="Healthcare OS")

    sms_enabled = models.BooleanField(default=False)
    sms_provider = models.CharField(max_length=50, blank=True, help_text="twilio, vonage, custom")
    sms_from_number = models.CharField(max_length=20, blank=True)

    whatsapp_enabled = models.BooleanField(default=False)
    whatsapp_from_number = models.CharField(max_length=20, blank=True)

    push_enabled = models.BooleanField(default=False)

    # Rate limits
    max_sms_per_day = models.IntegerField(default=100)
    max_email_per_hour = models.IntegerField(default=500)

    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "notifications_channel_config"

    def __str__(self):
        return f"Notification config for {self.tenant.name}"
