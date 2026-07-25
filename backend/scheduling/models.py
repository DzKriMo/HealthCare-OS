"""
Appointment and scheduling models — Sprint 3.

Core entities:
    PractitionerSchedule — recurring availability slots per practitioner.
    Appointment — the central scheduling entity with status state machine.
    AppointmentRecurrence — RRULE-based recurrence configuration.
    WaitingListEntry — patient waitlist for preferred slots.
    Room — physical room/resource for scheduling.
"""
import uuid
import datetime
from django.db import models
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.utils import timezone

from tenancy.models import Tenant
from tenancy.managers import TenantScopedManager
from patients.models import Patient


# ═══════════════════════════════════════════════════════════════
# Room
# ═══════════════════════════════════════════════════════════════

class Room(models.Model):
    """Physical room or resource that can be scheduled."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="rooms")
    name = models.CharField(max_length=100)
    color = models.CharField(max_length=7, default="#6b7280", help_text="Hex color for calendar.")
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "scheduling_room"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "name"], name="unique_room_name_per_tenant"),
        ]

    def __str__(self):
        return f"{self.name}"


# ═══════════════════════════════════════════════════════════════
# Practitioner Schedule
# ═══════════════════════════════════════════════════════════════

class PractitionerSchedule(models.Model):
    """
    Recurring availability for a practitioner.

    Each entry defines a weekly recurring time block.
    Example: "Dr. Smith is available Mondays 9:00–17:00."
    """

    class DayOfWeek(models.IntegerChoices):
        MONDAY = 0, "Monday"
        TUESDAY = 1, "Tuesday"
        WEDNESDAY = 2, "Wednesday"
        THURSDAY = 3, "Thursday"
        FRIDAY = 4, "Friday"
        SATURDAY = 5, "Saturday"
        SUNDAY = 6, "Sunday"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="practitioner_schedules")
    practitioner = models.ForeignKey(
        "identity.User", on_delete=models.CASCADE, related_name="schedules",
    )
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, related_name="schedules")

    day_of_week = models.IntegerField(choices=DayOfWeek.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_duration_minutes = models.IntegerField(default=30, help_text="Duration of each bookable slot.")

    is_active = models.BooleanField(default=True)
    valid_from = models.DateField()
    valid_until = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "scheduling_practitioner_schedule"
        ordering = ["day_of_week", "start_time"]
        indexes = [
            models.Index(fields=["tenant", "practitioner"]),
            models.Index(fields=["tenant", "day_of_week"]),
        ]

    def __str__(self):
        return f"{self.practitioner.full_name} — {self.get_day_of_week_display()} {self.start_time}–{self.end_time}"

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time.")


# ═══════════════════════════════════════════════════════════════
# Appointment
# ═══════════════════════════════════════════════════════════════

class Appointment(models.Model):
    """
    Core appointment entity with status state machine.

    Status transitions:
        scheduled → confirmed → arrived → in_progress → completed
        scheduled → cancelled
        scheduled → no_show
        confirmed → cancelled
        confirmed → no_show
        arrived → cancelled (with reason)
    """

    class Status(models.TextChoices):
        SCHEDULED = "scheduled", "Scheduled"
        CONFIRMED = "confirmed", "Confirmed"
        ARRIVED = "arrived", "Arrived"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"
        NO_SHOW = "no_show", "No Show"

    class Type(models.TextChoices):
        CONSULTATION = "consultation", "Consultation"
        FOLLOW_UP = "follow_up", "Follow-Up"
        PROCEDURE = "procedure", "Procedure"
        EMERGENCY = "emergency", "Emergency"
        CHECKUP = "checkup", "Checkup"
        OTHER = "other", "Other"

    # Valid status transitions
    STATUS_TRANSITIONS = {
        Status.SCHEDULED: [Status.CONFIRMED, Status.ARRIVED, Status.CANCELLED, Status.NO_SHOW],
        Status.CONFIRMED: [Status.ARRIVED, Status.CANCELLED, Status.NO_SHOW],
        Status.ARRIVED: [Status.IN_PROGRESS, Status.CANCELLED],
        Status.IN_PROGRESS: [Status.COMPLETED],
        Status.COMPLETED: [],
        Status.CANCELLED: [Status.SCHEDULED],  # Rebook
        Status.NO_SHOW: [Status.SCHEDULED],     # Rebook
    }

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="appointments")

    # Participants
    patient = models.ForeignKey(
        Patient, on_delete=models.PROTECT, related_name="appointments",
    )
    practitioner = models.ForeignKey(
        "identity.User", on_delete=models.PROTECT, related_name="appointments",
    )

    # Time
    start_time = models.DateTimeField(db_index=True)
    end_time = models.DateTimeField()
    duration_minutes = models.IntegerField(editable=False, help_text="Auto-calculated from start/end.")

    # Classification
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.CONSULTATION)
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.SCHEDULED, db_index=True,
    )
    priority = models.CharField(
        max_length=10,
        choices=[("low", "Low"), ("normal", "Normal"), ("high", "High"), ("urgent", "Urgent")],
        default="normal",
    )

    # Details
    reason = models.TextField(blank=True, help_text="Chief complaint or reason for visit.")
    notes = models.TextField(blank=True, help_text="Internal notes (not shared with patient).")

    # Resource
    room = models.ForeignKey(Room, on_delete=models.SET_NULL, null=True, blank=True, related_name="appointments")
    color = models.CharField(max_length=7, blank=True, help_text="Override color for calendar display.")

    # Recurrence
    is_recurring = models.BooleanField(default=False)
    recurrence_rule = models.CharField(
        max_length=500, blank=True,
        help_text="RRULE string for recurring appointments.",
    )
    recurrence_group = models.UUIDField(
        null=True, blank=True,
        help_text="Shared UUID for all instances of a recurring series.",
    )
    is_recurrence_exception = models.BooleanField(
        default=False,
        help_text="True if this instance was modified from the recurrence pattern.",
    )

    # Online booking
    booked_online = models.BooleanField(default=False)
    booking_source = models.CharField(max_length=50, blank=True, help_text="web, phone, walk-in, app.")
    confirmation_code = models.CharField(max_length=20, blank=True)

    # Audit
    created_by = models.ForeignKey(
        "identity.User", on_delete=models.PROTECT, null=True, related_name="created_appointments",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Check-in tracking
    checked_in_at = models.DateTimeField(null=True, blank=True)
    checked_in_by = models.ForeignKey(
        "identity.User", on_delete=models.PROTECT, null=True, blank=True,
        related_name="checkins",
    )
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Cancellation
    cancelled_at = models.DateTimeField(null=True, blank=True)
    cancellation_reason = models.TextField(blank=True)
    cancelled_by = models.ForeignKey(
        "identity.User", on_delete=models.PROTECT, null=True, blank=True,
        related_name="cancelled_appointments",
    )

    objects = TenantScopedManager()

    class Meta:
        db_table = "scheduling_appointment"
        ordering = ["-start_time"]
        indexes = [
            models.Index(fields=["tenant", "start_time"]),
            models.Index(fields=["tenant", "patient"]),
            models.Index(fields=["tenant", "practitioner"]),
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["tenant", "start_time", "end_time"]),
        ]
        constraints = [
            models.CheckConstraint(
                condition=Q(start_time__lt=models.F("end_time")),
                name="appointment_start_before_end",
            ),
        ]

    def __str__(self):
        return (
            f"{self.patient.full_name} with {self.practitioner.full_name} "
            f"on {self.start_time:%Y-%m-%d %H:%M}"
        )

    def save(self, *args, **kwargs):
        """Auto-calculate duration and validate."""
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            self.duration_minutes = int(delta.total_seconds() / 60)
        super().save(*args, **kwargs)

    def clean(self):
        if self.start_time and self.end_time and self.start_time >= self.end_time:
            raise ValidationError("Start time must be before end time.")

    # ── Status Transitions ────────────────────────────────

    def can_transition_to(self, target_status: str) -> bool:
        """Check if a status transition is valid."""
        allowed = self.STATUS_TRANSITIONS.get(self.status, [])
        return target_status in allowed

    def transition_to(self, target_status: str, user=None, reason: str = "") -> None:
        """Attempt a status transition. Raises ValidationError if invalid."""
        if not self.can_transition_to(target_status):
            raise ValidationError(
                f"Cannot transition from '{self.status}' to '{target_status}'."
            )

        now = timezone.now()
        self.status = target_status

        if target_status == self.Status.ARRIVED:
            self.checked_in_at = now
            self.checked_in_by = user
        elif target_status == self.Status.IN_PROGRESS:
            self.started_at = now
        elif target_status == self.Status.COMPLETED:
            self.completed_at = now
        elif target_status == self.Status.CANCELLED:
            self.cancelled_at = now
            self.cancellation_reason = reason
            self.cancelled_by = user

        self.save(
            update_fields=[
                "status", "checked_in_at", "checked_in_by",
                "started_at", "completed_at", "cancelled_at",
                "cancellation_reason", "cancelled_by",
            ],
        )

    @classmethod
    def find_conflicts(cls, tenant, practitioner_id, start_time, end_time, exclude_id=None):
        """Find overlapping appointments for a practitioner."""
        qs = cls.objects.for_tenant(tenant).filter(
            practitioner_id=practitioner_id,
            start_time__lt=end_time,
            end_time__gt=start_time,
        ).exclude(status__in=[cls.Status.CANCELLED, cls.Status.NO_SHOW])

        if exclude_id:
            qs = qs.exclude(id=exclude_id)

        return qs

    @classmethod
    def has_conflict(cls, tenant, practitioner_id, start_time, end_time, exclude_id=None) -> bool:
        """Check if an appointment would conflict."""
        return cls.find_conflicts(tenant, practitioner_id, start_time, end_time, exclude_id).exists()


# ═══════════════════════════════════════════════════════════════
# Waiting List
# ═══════════════════════════════════════════════════════════════

class WaitingListEntry(models.Model):
    """
    Patient on the waiting list for an appointment slot.

    When a slot opens, the system can suggest matching waitlisted patients.
    """

    class Priority(models.TextChoices):
        LOW = "low", "Low"
        NORMAL = "normal", "Normal"
        HIGH = "high", "High"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="waiting_list")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="waiting_list_entries")

    preferred_practitioner = models.ForeignKey(
        "identity.User", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="waiting_list_entries",
    )
    preferred_date_start = models.DateField(null=True, blank=True)
    preferred_date_end = models.DateField(null=True, blank=True)
    preferred_time_of_day = models.CharField(
        max_length=20, blank=True,
        choices=[("morning", "Morning"), ("afternoon", "Afternoon"), ("evening", "Evening")],
    )
    appointment_type = models.CharField(
        max_length=20, choices=Appointment.Type.choices, default=Appointment.Type.CONSULTATION,
    )
    priority = models.CharField(max_length=10, choices=Priority.choices, default=Priority.NORMAL)
    reason = models.TextField(blank=True)
    notes = models.TextField(blank=True)

    is_fulfilled = models.BooleanField(default=False)
    fulfilled_appointment = models.ForeignKey(
        Appointment, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="fulfilled_waiting_entry",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "scheduling_waiting_list"
        ordering = ["-priority", "created_at"]
        verbose_name_plural = "waiting list entries"
        indexes = [
            models.Index(fields=["tenant"]),
            models.Index(fields=["tenant", "is_fulfilled"]),
            models.Index(fields=["tenant", "priority"]),
        ]

    def __str__(self):
        return f"{self.patient.full_name} — {self.get_appointment_type_display()} ({self.get_priority_display()})"


# ═══════════════════════════════════════════════════════════════
# Booking Token (self-service links)
# ═══════════════════════════════════════════════════════════════

class BookingToken(models.Model):
    """
    One-time token for patient self-service booking actions.

    Embedded in confirmation/SMS emails. Lets patients confirm,
    cancel, or reschedule without logging in.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    appointment = models.ForeignKey(Appointment, on_delete=models.CASCADE, related_name="booking_tokens")
    token = models.CharField(max_length=100, unique=True, db_index=True)
    action = models.CharField(max_length=20, choices=[
        ("confirm", "Confirm"), ("cancel", "Cancel"), ("reschedule", "Reschedule"),
    ])
    is_used = models.BooleanField(default=False)
    used_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "scheduling_booking_token"

    @property
    def is_valid(self) -> bool:
        from django.utils import timezone
        return not self.is_used and self.expires_at > timezone.now()

    @classmethod
    def generate(cls, appointment, action: str, validity_hours: int = 72):
        """Generate a new booking token."""
        import secrets
        from django.utils import timezone
        return cls.objects.create(
            appointment=appointment,
            token=secrets.token_urlsafe(32),
            action=action,
            expires_at=timezone.now() + timezone.timedelta(hours=validity_hours),
        )
