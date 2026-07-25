from django.urls import path
from . import views

app_name = "sync"

urlpatterns = [
    path("devices/register/", views.DeviceRegisterView.as_view(), name="device-register"),
    path("push/", views.SyncPushView.as_view(), name="sync-push"),
    path("pull/", views.SyncPullView.as_view(), name="sync-pull"),
    path("status/", views.SyncStatusView.as_view(), name="sync-status"),
    path("conflict-rules/", views.ConflictRulesView.as_view(), name="conflict-rules"),
]
