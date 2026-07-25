from django.urls import path
from . import views

app_name = "cardiology"

urlpatterns = [
    path("ecg/", views.ECGListView.as_view(), name="ecg-list"),
    path("echo/", views.EchoListView.as_view(), name="echo-list"),
    path("bp/", views.BPListView.as_view(), name="bp-list"),
    path("dashboard/", views.CVDashboardView.as_view(), name="dashboard"),
]
