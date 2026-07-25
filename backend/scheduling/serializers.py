"""
Serializers for appointment and scheduling domain.
"""
from django.utils import timezone
from rest_framework import serializers
from django.core.exceptions import ValidationError as DjangoValidationError

from .models import Appointment, PractitionerSchedule, WaitingListEntry, Room


# ── Room ────────────────────────────────────────────────────

class RoomSerializer(serializers.ModelSerializer):
    class Meta:
        model = Room
        fields = ["id", "name", "color", "is_active"]
        read_only_fields = ["id"]


# ── Practitioner Schedule ───────────────────────────────────

class PractitionerScheduleSerializer(serializers.ModelSerializer):
    practitioner_name = serializers.CharField(source="practitioner.full_name", read_only=True)

    class Meta:
        model = PractitionerSchedule
        fields = [
            "id", "practitioner", "practitioner_name", "day_of_week",
            "start_time", "end_time", "slot_duration_minutes",
            "is_active", "valid_from", "valid_until",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        tenant = self.context["request"].tenant
        return PractitionerSchedule.objects.create(tenant=tenant, **validated_data)


# ── Appointment ─────────────────────────────────────────────

class AppointmentListSerializer(serializers.ModelSerializer):
    """Compact representation for list/calendar views."""
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    practitioner_name = serializers.CharField(source="practitioner.full_name", read_only=True)
    room_name = serializers.CharField(source="room.name", read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id", "patient", "patient_name", "practitioner", "practitioner_name",
            "start_time", "end_time", "duration_minutes",
            "type", "status", "priority",
            "room", "room_name", "color",
            "is_recurring", "recurrence_group",
            "checked_in_at",
        ]


class AppointmentDetailSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    practitioner_name = serializers.CharField(source="practitioner.full_name", read_only=True)
    room_name = serializers.CharField(source="room.name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)
    available_transitions = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = [
            "id", "tenant", "patient", "patient_name",
            "practitioner", "practitioner_name",
            "start_time", "end_time", "duration_minutes",
            "type", "status", "priority",
            "reason", "notes",
            "room", "room_name", "color",
            "is_recurring", "recurrence_rule", "recurrence_group",
            "booked_online", "booking_source", "confirmation_code",
            "checked_in_at", "checked_in_by",
            "started_at", "completed_at",
            "cancelled_at", "cancellation_reason", "cancelled_by",
            "created_by", "created_by_name", "created_at", "updated_at",
            "available_transitions",
        ]
        read_only_fields = [
            "id", "tenant", "duration_minutes", "checked_in_at", "checked_in_by",
            "started_at", "completed_at", "cancelled_at", "cancelled_by",
            "created_by", "created_at", "updated_at",
        ]

    def get_available_transitions(self, obj) -> list[str]:
        return obj.STATUS_TRANSITIONS.get(obj.status, [])


class AppointmentCreateSerializer(serializers.ModelSerializer):
    """Create a new appointment with conflict detection."""
    id = serializers.UUIDField(read_only=True)
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    practitioner_name = serializers.CharField(source="practitioner.full_name", read_only=True)
    status = serializers.CharField(read_only=True)

    class Meta:
        model = Appointment
        fields = [
            "id", "patient", "patient_name", "practitioner", "practitioner_name",
            "start_time", "end_time", "type", "priority",
            "reason", "notes", "room", "color",
            "is_recurring", "recurrence_rule",
            "status", "booked_online", "booking_source",
        ]

    def validate(self, attrs):
        tenant = self.context["request"].tenant
        practitioner_id = attrs["practitioner"].id if hasattr(attrs["practitioner"], "id") else attrs["practitioner"]
        start_time = attrs["start_time"]
        end_time = attrs["end_time"]

        # Check for conflicts
        if Appointment.has_conflict(tenant, practitioner_id, start_time, end_time):
            raise serializers.ValidationError(
                "This time slot conflicts with an existing appointment for this practitioner."
            )

        return attrs

    def create(self, validated_data):
        tenant = self.context["request"].tenant
        user = self.context["request"].user

        # Generate confirmation code for online bookings
        if validated_data.get("booked_online"):
            import secrets
            validated_data["confirmation_code"] = secrets.token_hex(4).upper()

        return Appointment.objects.create(
            tenant=tenant,
            created_by=user,
            **validated_data,
        )


class AppointmentUpdateSerializer(serializers.ModelSerializer):
    """Update appointment details."""

    class Meta:
        model = Appointment
        fields = [
            "start_time", "end_time", "type", "priority",
            "reason", "notes", "room", "color",
        ]

    def validate(self, attrs):
        # If times changed, re-check conflicts
        instance = self.instance
        new_start = attrs.get("start_time", instance.start_time)
        new_end = attrs.get("end_time", instance.end_time)
        practitioner = instance.practitioner

        if (new_start != instance.start_time or new_end != instance.end_time):
            tenant = self.context["request"].tenant
            if Appointment.has_conflict(tenant, practitioner.id, new_start, new_end, exclude_id=instance.id):
                raise serializers.ValidationError(
                    "This time slot conflicts with an existing appointment."
                )

        return attrs


class AppointmentStatusTransitionSerializer(serializers.Serializer):
    """Transition an appointment to a new status."""
    target_status = serializers.ChoiceField(choices=Appointment.Status.choices)
    reason = serializers.CharField(required=False, allow_blank=True, max_length=1000)

    def validate(self, attrs):
        appointment = self.context["appointment"]
        target = attrs["target_status"]

        if not appointment.can_transition_to(target):
            raise serializers.ValidationError(
                f"Cannot transition from '{appointment.status}' to '{target}'."
            )
        return attrs


# ── Calendar ────────────────────────────────────────────────

class CalendarQuerySerializer(serializers.Serializer):
    """Query params for calendar views."""
    date = serializers.DateField(required=False, help_text="Center date (default: today).")
    view = serializers.ChoiceField(
        choices=["day", "week", "month"], default="week",
    )
    practitioner_id = serializers.UUIDField(required=False)
    room_id = serializers.UUIDField(required=False)
    status = serializers.CharField(required=False)


class CalendarSlotSerializer(serializers.Serializer):
    """A time slot on the calendar (booked or available)."""
    start_time = serializers.DateTimeField()
    end_time = serializers.DateTimeField()
    practitioner_id = serializers.UUIDField()
    practitioner_name = serializers.CharField()
    is_available = serializers.BooleanField()
    appointment = AppointmentListSerializer(allow_null=True)


# ── Queue Board ─────────────────────────────────────────────

class QueueBoardSerializer(serializers.ModelSerializer):
    """Real-time view of today's appointments for queue display."""
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    practitioner_name = serializers.CharField(source="practitioner.full_name", read_only=True)
    room_name = serializers.CharField(source="room.name", read_only=True)
    wait_time_minutes = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = [
            "id", "patient", "patient_name", "practitioner_name",
            "start_time", "end_time", "type", "status", "priority",
            "room_name", "checked_in_at",
            "wait_time_minutes",
        ]

    def get_wait_time_minutes(self, obj) -> int | None:
        """Minutes since scheduled start or check-in."""
        if obj.checked_in_at:
            delta = timezone.now() - obj.checked_in_at
            return int(delta.total_seconds() / 60)
        if obj.status == Appointment.Status.SCHEDULED and obj.start_time <= timezone.now():
            delta = timezone.now() - obj.start_time
            return int(delta.total_seconds() / 60)
        return None


# ── Waiting List ────────────────────────────────────────────

class WaitingListSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    practitioner_name = serializers.CharField(
        source="preferred_practitioner.full_name", read_only=True,
    )

    class Meta:
        model = WaitingListEntry
        fields = [
            "id", "patient", "patient_name",
            "preferred_practitioner", "practitioner_name",
            "preferred_date_start", "preferred_date_end",
            "preferred_time_of_day", "appointment_type",
            "priority", "reason", "notes",
            "is_fulfilled", "created_at",
        ]
        read_only_fields = ["id", "is_fulfilled", "created_at"]


class WaitingListCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = WaitingListEntry
        fields = [
            "patient", "preferred_practitioner",
            "preferred_date_start", "preferred_date_end",
            "preferred_time_of_day", "appointment_type",
            "priority", "reason", "notes",
        ]

    def create(self, validated_data):
        tenant = self.context["request"].tenant
        return WaitingListEntry.objects.create(tenant=tenant, **validated_data)
