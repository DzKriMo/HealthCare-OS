"""
Appointment and scheduling views — Sprint 3.

CRUD, calendar views, queue board, waiting list, check-in workflow,
online booking (public), and status transitions.
"""
import datetime
from django.utils import timezone
from rest_framework import generics, status, views, permissions
from rest_framework.response import Response
from rest_framework.exceptions import NotFound, ValidationError
from drf_spectacular.utils import extend_schema

from tenancy.permissions import HasTenantAccess, TenantPermissionRequired
from .models import Appointment, PractitionerSchedule, WaitingListEntry, Room
from . import serializers


# ═══════════════════════════════════════════════════════════════
# Room Management
# ═══════════════════════════════════════════════════════════════

@extend_schema(tags=["scheduling"])
class RoomListView(generics.ListCreateAPIView):
    serializer_class = serializers.RoomSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "appointments.read"

    def get_queryset(self):
        return Room.objects.for_tenant(self.request.tenant).filter(is_active=True)

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.tenant)


# ═══════════════════════════════════════════════════════════════
# Practitioner Schedule
# ═══════════════════════════════════════════════════════════════

@extend_schema(tags=["scheduling"])
class PractitionerScheduleListView(generics.ListCreateAPIView):
    serializer_class = serializers.PractitionerScheduleSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "appointments.read"

    def get_queryset(self):
        return PractitionerSchedule.objects.for_tenant(self.request.tenant).filter(
            is_active=True,
        ).select_related("practitioner")


@extend_schema(tags=["scheduling"])
class PractitionerScheduleDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.PractitionerScheduleSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "appointments.edit"

    def get_queryset(self):
        return PractitionerSchedule.objects.for_tenant(self.request.tenant)


# ═══════════════════════════════════════════════════════════════
# Appointments
# ═══════════════════════════════════════════════════════════════

@extend_schema(tags=["appointments"])
class AppointmentListView(generics.ListCreateAPIView):
    """List appointments (with date range filters) or create a new one."""
    permission_classes = [HasTenantAccess, TenantPermissionRequired]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return serializers.AppointmentCreateSerializer
        return serializers.AppointmentListSerializer

    def get_queryset(self):
        qs = Appointment.objects.for_tenant(self.request.tenant).select_related(
            "patient", "practitioner", "room",
        )

        # Date range filter
        date_from = self.request.query_params.get("from")
        date_to = self.request.query_params.get("to")
        if date_from:
            qs = qs.filter(start_time__gte=date_from)
        if date_to:
            qs = qs.filter(end_time__lte=date_to)

        # Filters
        practitioner_id = self.request.query_params.get("practitioner")
        if practitioner_id:
            qs = qs.filter(practitioner_id=practitioner_id)

        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)

        patient_id = self.request.query_params.get("patient")
        if patient_id:
            qs = qs.filter(patient_id=patient_id)

        return qs.order_by("start_time")

    def get_required_permission(self):
        if self.request.method == "POST":
            return "appointments.create"
        return "appointments.read"


@extend_schema(tags=["appointments"])
class AppointmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Get, update, or cancel an appointment."""
    permission_classes = [HasTenantAccess, TenantPermissionRequired]

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return serializers.AppointmentUpdateSerializer
        return serializers.AppointmentDetailSerializer

    def get_queryset(self):
        return Appointment.objects.for_tenant(self.request.tenant).select_related(
            "patient", "practitioner", "room", "created_by",
        )

    def get_required_permission(self):
        if self.request.method == "GET":
            return "appointments.read"
        return "appointments.edit"

    def perform_destroy(self, instance):
        """Cancel rather than hard-delete."""
        instance.transition_to(
            Appointment.Status.CANCELLED,
            user=self.request.user,
            reason="Cancelled via API",
        )


@extend_schema(tags=["appointments"], summary="Transition appointment status")
class AppointmentStatusTransitionView(generics.GenericAPIView):
    """
    Transition an appointment through its status state machine.

    POST /api/appointments/{id}/transition/
    Body: {"target_status": "arrived", "reason": "..."}
    """
    serializer_class = serializers.AppointmentStatusTransitionSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "appointments.edit"

    def post(self, request, pk):
        try:
            appointment = Appointment.objects.for_tenant(request.tenant).get(pk=pk)
        except Appointment.DoesNotExist:
            raise NotFound("Appointment not found.")

        serializer = self.get_serializer(
            data=request.data, context={"appointment": appointment},
        )
        serializer.is_valid(raise_exception=True)

        appointment.transition_to(
            serializer.validated_data["target_status"],
            user=request.user,
            reason=serializer.validated_data.get("reason", ""),
        )

        return Response(
            serializers.AppointmentDetailSerializer(appointment).data,
        )


# ═══════════════════════════════════════════════════════════════
# Calendar Views
# ═══════════════════════════════════════════════════════════════

@extend_schema(tags=["scheduling"], summary="Get calendar data for a date range")
class CalendarView(generics.GenericAPIView):
    """
    Aggregated calendar data for day/week/month views.

    GET /api/appointments/calendar/?date=2024-01-15&view=week&practitioner=<uuid>
    """
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "appointments.read"

    def get(self, request):
        query_serializer = serializers.CalendarQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        params = query_serializer.validated_data

        date = params.get("date") or timezone.now().date()
        view = params.get("view", "week")

        # Calculate date range
        date_range = self._get_date_range(date, view)

        # Get appointments for range
        qs = Appointment.objects.for_tenant(request.tenant).filter(
            start_time__lt=date_range["end"],
            end_time__gt=date_range["start"],
        ).exclude(status__in=[Appointment.Status.CANCELLED, Appointment.Status.NO_SHOW])

        if params.get("practitioner_id"):
            qs = qs.filter(practitioner_id=params["practitioner_id"])
        if params.get("room_id"):
            qs = qs.filter(room_id=params["room_id"])
        if params.get("status"):
            qs = qs.filter(status=params["status"])

        appointments = serializers.AppointmentListSerializer(qs, many=True).data

        return Response({
            "date": str(date),
            "view": view,
            "range": {
                "start": date_range["start"].isoformat(),
                "end": date_range["end"].isoformat(),
            },
            "appointments": appointments,
            "total": len(appointments),
        })

    def _get_date_range(self, date, view: str) -> dict:
        """Calculate start/end for day/week/month views."""
        if view == "day":
            start = datetime.datetime.combine(date, datetime.time.min)
            end = start + datetime.timedelta(days=1)
        elif view == "month":
            start = datetime.datetime.combine(
                date.replace(day=1), datetime.time.min,
            )
            # Go to first day of next month
            if date.month == 12:
                next_month = date.replace(year=date.year + 1, month=1, day=1)
            else:
                next_month = date.replace(month=date.month + 1, day=1)
            end = datetime.datetime.combine(next_month, datetime.time.min)
        else:  # week
            # Start from Monday
            weekday = date.weekday()
            monday = date - datetime.timedelta(days=weekday)
            start = datetime.datetime.combine(monday, datetime.time.min)
            end = start + datetime.timedelta(days=7)

        return {"start": start, "end": end}


# ═══════════════════════════════════════════════════════════════
# Queue Board
# ═══════════════════════════════════════════════════════════════

@extend_schema(tags=["scheduling"], summary="Get today's queue board")
class QueueBoardView(generics.GenericAPIView):
    """
    Real-time queue board for reception/wall display.

    Returns today's appointments grouped by practitioner/room
    with status indicators and wait times.
    """
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "appointments.read"

    def get(self, request):
        today = timezone.now().date()
        start = datetime.datetime.combine(today, datetime.time.min)
        end = start + datetime.timedelta(days=1)

        qs = Appointment.objects.for_tenant(request.tenant).filter(
            start_time__gte=start,
            start_time__lt=end,
        ).exclude(
            status__in=[Appointment.Status.CANCELLED],
        ).select_related("patient", "practitioner", "room").order_by("start_time")

        # Group by practitioner
        by_practitioner = {}
        for appt in qs:
            key = str(appt.practitioner_id)
            if key not in by_practitioner:
                by_practitioner[key] = {
                    "practitioner_id": key,
                    "practitioner_name": appt.practitioner.full_name,
                    "appointments": [],
                    "stats": {
                        "scheduled": 0, "arrived": 0, "in_progress": 0,
                        "completed": 0, "no_show": 0,
                    },
                }
            data = serializers.QueueBoardSerializer(appt).data
            by_practitioner[key]["appointments"].append(data)
            status = appt.status
            if status in by_practitioner[key]["stats"]:
                by_practitioner[key]["stats"][status] += 1

        return Response({
            "date": str(today),
            "total_appointments": qs.count(),
            "queues": list(by_practitioner.values()),
        })


# ═══════════════════════════════════════════════════════════════
# Waiting List
# ═══════════════════════════════════════════════════════════════

@extend_schema(tags=["scheduling"])
class WaitingListView(generics.ListCreateAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "appointments.read"

    def get_serializer_class(self):
        if self.request.method == "POST":
            return serializers.WaitingListCreateSerializer
        return serializers.WaitingListSerializer

    def get_queryset(self):
        return WaitingListEntry.objects.for_tenant(self.request.tenant).filter(
            is_fulfilled=False,
        ).select_related("patient", "preferred_practitioner")


@extend_schema(tags=["scheduling"])
class WaitingListDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.WaitingListSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "appointments.edit"

    def get_queryset(self):
        return WaitingListEntry.objects.for_tenant(self.request.tenant)

    def perform_destroy(self, instance):
        instance.is_fulfilled = True
        instance.save(update_fields=["is_fulfilled"])


# ═══════════════════════════════════════════════════════════════
# Online Booking (public)
# ═══════════════════════════════════════════════════════════════

@extend_schema(
    tags=["scheduling"],
    summary="Get available slots for online booking",
)
class AvailableSlotsView(generics.GenericAPIView):
    """
    Public endpoint — get available appointment slots.

    GET /api/appointments/slots/?date=2024-01-15&practitioner=<uuid>
    """
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def get(self, request):
        date_str = request.query_params.get("date")
        practitioner_id = request.query_params.get("practitioner")

        if not date_str:
            return Response(
                {"error": "date parameter is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            date = datetime.date.fromisoformat(date_str)
        except ValueError:
            return Response({"error": "Invalid date format."}, status=status.HTTP_400_BAD_REQUEST)

        # Get tenant from X-Tenant header (required for public booking)
        tenant_slug = request.META.get("HTTP_X_TENANT_SLUG")
        if not tenant_slug:
            return Response({"error": "Tenant is required."}, status=status.HTTP_400_BAD_REQUEST)

        from tenancy.models import Tenant
        try:
            tenant = Tenant.objects.get(slug=tenant_slug, is_active=True)
        except Tenant.DoesNotExist:
            return Response({"error": "Tenant not found."}, status=status.HTTP_404_NOT_FOUND)

        # Generate available slots
        slots = self._get_available_slots(tenant, date, practitioner_id)
        return Response({"date": date_str, "slots": slots})

    def _get_available_slots(self, tenant, date, practitioner_id=None) -> list[dict]:
        """Generate time slots based on practitioner schedules minus booked appointments."""
        day_of_week = date.weekday()
        schedules = PractitionerSchedule.objects.for_tenant(tenant).filter(
            day_of_week=day_of_week, is_active=True,
        )
        if practitioner_id:
            schedules = schedules.filter(practitioner_id=practitioner_id)

        day_start = datetime.datetime.combine(date, datetime.time.min)
        day_end = day_start + datetime.timedelta(days=1)

        # Get booked appointments for the day
        booked_qs = Appointment.objects.for_tenant(tenant).filter(
            start_time__gte=day_start,
            start_time__lt=day_end,
        ).exclude(status__in=[Appointment.Status.CANCELLED, Appointment.Status.NO_SHOW])

        booked_by_practitioner = {}
        for appt in booked_qs:
            pid = str(appt.practitioner_id)
            if pid not in booked_by_practitioner:
                booked_by_practitioner[pid] = []
            booked_by_practitioner[pid].append({
                "start": appt.start_time,
                "end": appt.end_time,
            })

        slots = []
        for schedule in schedules.select_related("practitioner"):
            pid = str(schedule.practitioner_id)
            current = datetime.datetime.combine(date, schedule.start_time)
            end = datetime.datetime.combine(date, schedule.end_time)
            booked = booked_by_practitioner.get(pid, [])

            while current + datetime.timedelta(minutes=schedule.slot_duration_minutes) <= end:
                slot_end = current + datetime.timedelta(minutes=schedule.slot_duration_minutes)
                is_available = not any(
                    b["start"] < slot_end and b["end"] > current for b in booked
                )
                slots.append({
                    "start_time": current.isoformat(),
                    "end_time": slot_end.isoformat(),
                    "practitioner_id": pid,
                    "practitioner_name": schedule.practitioner.full_name,
                    "is_available": is_available,
                })
                current = slot_end

        return slots


@extend_schema(
    tags=["scheduling"],
    summary="Book an appointment online (public)",
)
class OnlineBookingView(generics.GenericAPIView):
    """
    Public endpoint — book an appointment.

    POST /api/appointments/book/
    """
    permission_classes = [permissions.AllowAny]
    authentication_classes = []
    serializer_class = serializers.AppointmentCreateSerializer

    def post(self, request):
        # Resolve tenant
        tenant_slug = request.META.get("HTTP_X_TENANT_SLUG")
        if not tenant_slug:
            return Response({"error": "Tenant is required."}, status=status.HTTP_400_BAD_REQUEST)

        from tenancy.models import Tenant
        try:
            tenant = Tenant.objects.get(slug=tenant_slug, is_active=True)
        except Tenant.DoesNotExist:
            return Response({"error": "Tenant not found."}, status=status.HTTP_404_NOT_FOUND)

        # Inject tenant into serializer context
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        # Validate patient exists and belongs to this tenant
        patient_id = serializer.validated_data["patient"].id
        from patients.models import Patient
        try:
            Patient.objects.for_tenant(tenant).get(pk=patient_id)
        except Patient.DoesNotExist:
            return Response({"error": "Patient not found."}, status=status.HTTP_404_NOT_FOUND)

        appointment = Appointment.objects.create(
            tenant=tenant,
            booked_online=True,
            booking_source="web",
            **serializer.validated_data,
        )

        return Response(
            serializers.AppointmentDetailSerializer(appointment).data,
            status=status.HTTP_201_CREATED,
        )


# ═══════════════════════════════════════════════════════════════
# Booking Self-Service (token-authenticated)
# ═══════════════════════════════════════════════════════════════

@extend_schema(tags=["scheduling"], summary="Self-service booking action via token")
class BookingSelfServiceView(generics.GenericAPIView):
    """
    Patient self-service via tokens embedded in emails/SMS.

    POST /api/appointments/self-service/
    Body: {"token": "...", "action": "confirm"|"cancel"}
    """
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        token_str = request.data.get("token")
        action = request.data.get("action")
        reason = request.data.get("reason", "")

        if not token_str or not action:
            return Response(
                {"error": "token and action are required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        from .models import BookingToken
        try:
            booking_token = BookingToken.objects.get(token=token_str)
        except BookingToken.DoesNotExist:
            return Response({"error": "Invalid token."}, status=status.HTTP_404_NOT_FOUND)

        if not booking_token.is_valid:
            return Response({"error": "Token expired or already used."}, status=status.HTTP_400_BAD_REQUEST)

        appointment = booking_token.appointment

        if action == "confirm":
            appointment.transition_to(Appointment.Status.CONFIRMED)
            booking_token.is_used = True
            booking_token.used_at = timezone.now()
            booking_token.save()

        elif action == "cancel":
            appointment.transition_to(
                Appointment.Status.CANCELLED,
                reason=reason or "Cancelled by patient via self-service.",
            )
            booking_token.is_used = True
            booking_token.used_at = timezone.now()
            booking_token.save()

        elif action == "reschedule":
            new_time = request.data.get("new_start_time")
            if not new_time:
                return Response({"error": "new_start_time is required for reschedule."}, status=status.HTTP_400_BAD_REQUEST)

            appointment.start_time = new_time
            appointment.end_time = (
                timezone.datetime.fromisoformat(new_time)
                + timezone.timedelta(minutes=appointment.duration_minutes)
            )
            appointment.status = Appointment.Status.SCHEDULED
            appointment.save()
            booking_token.is_used = True
            booking_token.used_at = timezone.now()
            booking_token.save()

        else:
            return Response({"error": f"Unknown action: {action}"}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            "message": f"Appointment {action}ed successfully.",
            "appointment_id": str(appointment.id),
            "status": appointment.status,
        })
