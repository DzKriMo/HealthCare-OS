"""Django Admin for scheduling models."""
from django.contrib import admin
from .models import Appointment, PractitionerSchedule, WaitingListEntry, Room


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ["patient", "practitioner", "start_time", "type", "status", "tenant"]
    list_filter = ["status", "type", "tenant", "start_time"]
    search_fields = ["patient__first_name", "patient__last_name", "reason"]
    readonly_fields = ["id", "duration_minutes", "checked_in_at", "started_at", "completed_at", "created_at", "updated_at"]


@admin.register(PractitionerSchedule)
class PractitionerScheduleAdmin(admin.ModelAdmin):
    list_display = ["practitioner", "day_of_week", "start_time", "end_time", "is_active"]


@admin.register(WaitingListEntry)
class WaitingListEntryAdmin(admin.ModelAdmin):
    list_display = ["patient", "priority", "is_fulfilled", "created_at"]
    list_filter = ["priority", "is_fulfilled"]


@admin.register(Room)
class RoomAdmin(admin.ModelAdmin):
    list_display = ["name", "tenant", "is_active"]
