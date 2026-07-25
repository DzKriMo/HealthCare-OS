from django.urls import path
from . import views

app_name = "telemedicine"

urlpatterns = [
    path("consultations/", views.ConsultationListView.as_view(), name="consultation-list"),
    path("consultations/<uuid:pk>/", views.ConsultationDetailView.as_view(), name="consultation-detail"),
    path("consultations/<uuid:pk>/start/", views.ConsultationStartView.as_view(), name="consultation-start"),
    path("consultations/<uuid:pk>/end/", views.ConsultationEndView.as_view(), name="consultation-end"),
    path("chat/rooms/", views.ChatRoomListView.as_view(), name="chat-room-list"),
    path("chat/rooms/<uuid:room_id>/messages/", views.ChatMessageListView.as_view(), name="chat-message-list"),
    path("chat/rooms/<uuid:room_id>/messages/<uuid:pk>/read/", views.ChatMessageMarkReadView.as_view(), name="chat-message-read"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
]
