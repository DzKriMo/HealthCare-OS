from django.urls import path
from . import views

app_name = "ai_diagnostics"

urlpatterns = [
    path("settings/", views.AISettingsView.as_view(), name="settings"),
    path("suggest/icd10/", views.ICD10SuggestView.as_view(), name="suggest-icd10"),
    path("suggest/soap/", views.SOAPDraftView.as_view(), name="suggest-soap"),
    path("suggest/drug-interaction/", views.DrugInteractionView.as_view(), name="suggest-drug-interaction"),
    path("suggest/symptom-analysis/", views.SymptomAnalysisView.as_view(), name="suggest-symptom"),
    path("suggest/treatment-plan/", views.TreatmentPlanView.as_view(), name="suggest-treatment"),
    path("suggest/cpt/", views.CPTSuggestView.as_view(), name="suggest-cpt"),
    path("suggest/prescription/", views.PrescriptionDraftView.as_view(), name="suggest-prescription"),
    path("suggestions/", views.SuggestionListView.as_view(), name="suggestion-list"),
    path("suggestions/<uuid:pk>/feedback/", views.SuggestionFeedbackView.as_view(), name="suggestion-feedback"),
    path("audit-log/", views.AuditLogListView.as_view(), name="audit-log"),
    path("dashboard/", views.DashboardView.as_view(), name="dashboard"),
]
