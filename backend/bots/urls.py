from django.urls import path
from . import views

app_name = "bots"

urlpatterns = [
    path("settings/", views.BotConfigView.as_view(), name="settings"),
    path("whatsapp/send/", views.WhatsAppSendView.as_view(), name="whatsapp-send"),
    path("whatsapp/webhook/", views.WhatsAppWebhookView.as_view(), name="whatsapp-webhook"),
    path("voice/call/", views.VoiceCallView.as_view(), name="voice-call"),
    path("voice/twiml/", views.VoiceTwimlView.as_view(), name="voice-twiml"),
    path("voice/status/", views.VoiceStatusView.as_view(), name="voice-status"),
    path("reminder/", views.AppointmentReminderView.as_view(), name="reminder"),
    path("conversations/", views.ConversationListView.as_view(), name="conversation-list"),
    path("conversations/<uuid:pk>/", views.ConversationDetailView.as_view(), name="conversation-detail"),
    path("conversations/<uuid:pk>/messages/", views.ConversationMessageListView.as_view(), name="conversation-messages"),
    path("calls/", views.VoiceCallLogListView.as_view(), name="call-list"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
]
