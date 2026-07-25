from django.urls import path
from . import views

app_name = "pharmacy"

urlpatterns = [
    path("prescriptions/", views.PrescriptionListView.as_view(), name="rx-list"),
    path("prescriptions/<uuid:pk>/", views.PrescriptionDetailView.as_view(), name="rx-detail"),
    path("dispense/", views.DispenseListView.as_view(), name="dispense-list"),
    path("pos/", views.PharmacyPOSView.as_view(), name="pharmacy-pos"),
    path("controlled/", views.ControlledLogListView.as_view(), name="controlled-log"),
    path("dashboard/", views.PharmacyDashboardView.as_view(), name="dashboard"),
]
