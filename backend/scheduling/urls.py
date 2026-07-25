"""
Scheduling URL configuration.
"""
from django.urls import path
from . import views

app_name = "scheduling"

urlpatterns = [
    # Rooms
    path("rooms/", views.RoomListView.as_view(), name="room-list"),

    # Practitioner schedules
    path("schedules/", views.PractitionerScheduleListView.as_view(), name="schedule-list"),
    path("schedules/<uuid:pk>/", views.PractitionerScheduleDetailView.as_view(), name="schedule-detail"),

    # Calendar
    path("calendar/", views.CalendarView.as_view(), name="calendar"),

    # Queue board
    path("queue/", views.QueueBoardView.as_view(), name="queue-board"),

    # Appointments
    path("", views.AppointmentListView.as_view(), name="appointment-list"),
    path("<uuid:pk>/", views.AppointmentDetailView.as_view(), name="appointment-detail"),
    path("<uuid:pk>/transition/", views.AppointmentStatusTransitionView.as_view(), name="appointment-transition"),

    # Waiting list
    path("waiting-list/", views.WaitingListView.as_view(), name="waiting-list"),
    path("waiting-list/<uuid:pk>/", views.WaitingListDetailView.as_view(), name="waiting-list-detail"),

    # Online booking (public)
    path("slots/", views.AvailableSlotsView.as_view(), name="available-slots"),
    path("book/", views.OnlineBookingView.as_view(), name="online-booking"),
    path("self-service/", views.BookingSelfServiceView.as_view(), name="booking-self-service"),
]
