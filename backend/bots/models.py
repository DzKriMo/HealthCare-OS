import uuid
from django.db import models
from django.utils import timezone
from tenancy.models import Tenant
from tenancy.managers import TenantScopedManager


class BotConfig(models.Model):
    tenant = models.OneToOneField(Tenant, on_delete=models.CASCADE, related_name="bot_config", primary_key=True)
    whatsapp_enabled = models.BooleanField(default=False)
    whatsapp_from_number = models.CharField(max_length=30, blank=True)
    whatsapp_business_account_id = models.CharField(max_length=200, blank=True)
    voice_enabled = models.BooleanField(default=False)
    voice_from_number = models.CharField(max_length=30, blank=True)
    voice_language = models.CharField(max_length=10, default="en-US", help_text="TTS language code")
    auto_reply_enabled = models.BooleanField(default=True, help_text="Auto-reply to incoming WhatsApp messages")
    auto_reply_message = models.TextField(
        default="Thank you for your message. We'll get back to you shortly.",
        help_text="Default auto-reply when bot cannot handle the query",
    )
    appointment_reminders_enabled = models.BooleanField(default=True)
    appointment_reminder_hours_before = models.IntegerField(default=24)
    follow_up_enabled = models.BooleanField(default=True)
    business_hours_only = models.BooleanField(default=True)
    business_hours_start = models.TimeField(default="09:00")
    business_hours_end = models.TimeField(default="17:00")
    timezone = models.CharField(max_length=50, default="UTC")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "bots_config"

    def __str__(self):
        return f"Bot config for {self.tenant}"


class WhatsAppConversation(models.Model):
    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        RESOLVED = "resolved", "Resolved"
        ESCALATED = "escalated", "Escalated to Staff"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="whatsapp_conversations")
    patient = models.ForeignKey("patients.Patient", on_delete=models.SET_NULL, null=True, blank=True)
    customer_phone = models.CharField(max_length=30, db_index=True)
    customer_name = models.CharField(max_length=200, blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    is_bot_handled = models.BooleanField(default=True)
    assigned_to = models.ForeignKey("identity.User", on_delete=models.SET_NULL, null=True, blank=True)
    last_message_at = models.DateTimeField(auto_now=True)
    message_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "bots_whatsapp_conversation"
        ordering = ["-last_message_at"]
        indexes = [
            models.Index(fields=["tenant", "customer_phone"]),
            models.Index(fields=["tenant", "status"]),
        ]

    def __str__(self):
        return f"WhatsApp {self.customer_phone} ({self.status})"


class WhatsAppMessage(models.Model):
    class Direction(models.TextChoices):
        INBOUND = "inbound", "Inbound"
        OUTBOUND = "outbound", "Outbound"

    class MessageType(models.TextChoices):
        TEXT = "text", "Text"
        TEMPLATE = "template", "Template"
        IMAGE = "image", "Image"
        DOCUMENT = "document", "Document"
        INTERACTIVE = "interactive", "Interactive"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="whatsapp_messages")
    conversation = models.ForeignKey(WhatsAppConversation, on_delete=models.CASCADE, related_name="messages")
    direction = models.CharField(max_length=10, choices=Direction.choices)
    message_type = models.CharField(max_length=20, choices=MessageType.choices, default=MessageType.TEXT)
    content = models.TextField(blank=True)
    media_url = models.URLField(max_length=500, blank=True)
    template_name = models.CharField(max_length=100, blank=True)
    twilio_message_sid = models.CharField(max_length=100, blank=True, db_index=True)
    status = models.CharField(max_length=30, blank=True, help_text="twilio delivery status")
    is_bot_reply = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "bots_whatsapp_message"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["conversation", "created_at"]),
            models.Index(fields=["twilio_message_sid"]),
        ]

    def __str__(self):
        return f"{self.direction} msg in {self.conversation.id}"


class VoiceCallLog(models.Model):
    class Direction(models.TextChoices):
        OUTBOUND = "outbound", "Outbound"
        INBOUND = "inbound", "Inbound"

    class Status(models.TextChoices):
        QUEUED = "queued", "Queued"
        RINGING = "ringing", "Ringing"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        BUSY = "busy", "Busy"
        FAILED = "failed", "Failed"
        NO_ANSWER = "no_answer", "No Answer"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="voice_calls")
    patient = models.ForeignKey("patients.Patient", on_delete=models.SET_NULL, null=True, blank=True)
    direction = models.CharField(max_length=10, choices=Direction.choices)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.QUEUED)
    to_number = models.CharField(max_length=30)
    from_number = models.CharField(max_length=30)
    duration_seconds = models.IntegerField(null=True, blank=True)
    purpose = models.CharField(max_length=100, blank=True, help_text="appointment_reminder, follow_up, etc.")
    twilio_call_sid = models.CharField(max_length=100, blank=True, db_index=True)
    recording_url = models.URLField(max_length=500, blank=True)
    transcription = models.TextField(blank=True)
    cost = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
    is_bot_call = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict)
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "bots_voice_call_log"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["twilio_call_sid"]),
        ]

    def __str__(self):
        return f"{self.direction} call to {self.to_number} ({self.status})"
