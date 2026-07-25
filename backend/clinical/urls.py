from django.urls import path
from . import views

app_name = "clinical"

urlpatterns = [
    path("encounters/", views.EncounterListView.as_view(), name="encounter-list"),
    path("encounters/<uuid:pk>/", views.EncounterDetailView.as_view(), name="encounter-detail"),
    path("encounters/<uuid:pk>/sign/", views.EncounterSignView.as_view(), name="encounter-sign"),
    path("diagnoses/", views.DiagnosisListView.as_view(), name="diagnosis-list"),
    path("referrals/", views.ReferralListView.as_view(), name="referral-list"),
    path("vitals/", views.VitalSignsListView.as_view(), name="vital-list"),
    path("vaccinations/", views.VaccinationListView.as_view(), name="vax-list"),
    path("history/", views.HistoryListView.as_view(), name="history"),
    path("dashboard/", views.ClinicalDashboardView.as_view(), name="dashboard"),
]
