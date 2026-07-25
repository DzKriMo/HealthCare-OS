import uuid
from django.db import models
from django.utils import timezone
from tenancy.models import Tenant
from tenancy.managers import TenantScopedManager


class VideoConsultation(models.Model):
    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        READY = "ready", "Ready"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        MISSED = "missed", "Missed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="video_consultations")
    appointment = models.ForeignKey(
        "scheduling.Appointment", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="video_consultations",
    )
    patient = models.ForeignKey("patients.Patient", on_delete=models.PROTECT, related_name="video_consultations")
    practitioner = models.ForeignKey("identity.User", on_delete=models.PROTECT, related_name="video_consultations")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.SCHEDULED, db_index=True)
    scheduled_at = models.DateTimeField()
    started_at = models.DateTimeField(null=True, blank=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    meeting_url = models.URLField(max_length=500, blank=True, help_text="Jitsi/Meet room URL")
    room_name = models.CharField(max_length=200, unique=True, help_text="Unique room identifier for video bridge")
    notes = models.TextField(blank=True)
    cancellation_reason = models.TextField(blank=True)
    created_by = models.ForeignKey("identity.User", on_delete=models.PROTECT, null=True, related_name="created_consultations")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "telemedicine_video_consultation"
        ordering = ["-scheduled_at"]
        indexes = [
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["tenant", "patient"]),
            models.Index(fields=["tenant", "practitioner"]),
        ]

    def __str__(self):
        return f"Consultation {self.patient} with {self.practitioner} @ {self.scheduled_at}"


class ChatRoom(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="chat_rooms")
    consultation = models.OneToOneField(
        VideoConsultation, on_delete=models.CASCADE, null=True, blank=True,
        related_name="chat_room",
    )
    participants = models.ManyToManyField("identity.User", related_name="chat_rooms")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "telemedicine_chat_room"
        ordering = ["-updated_at"]

    def __str__(self):
        return f"ChatRoom {self.id} ({self.participants.count()} participants)"


class ChatMessage(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room = models.ForeignKey(ChatRoom, on_delete=models.CASCADE, related_name="messages")
    sender = models.ForeignKey("identity.User", on_delete=models.PROTECT, related_name="sent_messages")
    content = models.TextField()
    attachment_url = models.URLField(max_length=500, blank=True)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "telemedicine_chat_message"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["room", "created_at"]),
        ]

    def __str__(self):
        return f"Message from {self.sender} in {self.room.id}"

    def mark_read(self):
        self.read_at = timezone.now()
        self.save(update_fields=["read_at"])
