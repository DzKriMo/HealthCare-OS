"""Dental module URLs."""
from django.urls import path
from . import views

app_name = "dental"

urlpatterns = [
    # Tooth chart
    path("chart/<uuid:patient_pk>/", views.ChartView.as_view(), name="chart"),
    path("tooth/<uuid:pk>/", views.ToothDetailView.as_view(), name="tooth-detail"),

    # Procedures
    path("procedures/", views.ProcedureListView.as_view(), name="procedure-list"),
    path("procedures/<uuid:pk>/", views.ProcedureDetailView.as_view(), name="procedure-detail"),

    # Implants & Crowns
    path("implants/", views.ImplantListView.as_view(), name="implant-list"),
    path("crowns/", views.CrownListView.as_view(), name="crown-list"),

    # Treatment plans
    path("plans/", views.TreatmentPlanListView.as_view(), name="plan-list"),
    path("plans/<uuid:pk>/", views.TreatmentPlanDetailView.as_view(), name="plan-detail"),

    # Dashboard
    path("dashboard/", views.DentalDashboardView.as_view(), name="dashboard"),
]
