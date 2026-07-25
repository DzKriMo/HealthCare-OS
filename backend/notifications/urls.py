"""Notification URLs."""
from django.urls import path
from . import views

app_name = "notifications"

urlpatterns = [
    path("templates/", views.TemplateListView.as_view(), name="template-list"),
    path("templates/<uuid:pk>/", views.TemplateDetailView.as_view(), name="template-detail"),
    path("events/", views.EventListView.as_view(), name="event-list"),
    path("send/", views.NotificationSendView.as_view(), name="notification-send"),
    path("config/", views.ChannelConfigView.as_view(), name="channel-config"),
]
