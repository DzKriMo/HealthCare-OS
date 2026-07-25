"""
Patient domain URL configuration.
"""
from django.urls import path
from . import views

app_name = "patients"

urlpatterns = [
    # Patient CRUD
    path("", views.PatientListView.as_view(), name="patient-list"),
    path("search/", views.PatientSearchView.as_view(), name="patient-search"),
    path("<uuid:pk>/", views.PatientDetailView.as_view(), name="patient-detail"),
    path("<uuid:pk>/timeline/", views.PatientTimelineView.as_view(), name="patient-timeline"),

    # Medical History (nested under patient)
    path(
        "<uuid:patient_pk>/history/",
        views.MedicalHistoryListView.as_view(),
        name="medical-history-list",
    ),
    path(
        "history/<uuid:pk>/",
        views.MedicalHistoryDetailView.as_view(),
        name="medical-history-detail",
    ),

    # Allergies (nested under patient)
    path(
        "<uuid:patient_pk>/allergies/",
        views.AllergyListView.as_view(),
        name="allergy-list",
    ),
    path(
        "allergies/<uuid:pk>/",
        views.AllergyDetailView.as_view(),
        name="allergy-detail",
    ),

    # Medications (nested under patient)
    path(
        "<uuid:patient_pk>/medications/",
        views.MedicationListView.as_view(),
        name="medication-list",
    ),
    path(
        "medications/<uuid:pk>/",
        views.MedicationDetailView.as_view(),
        name="medication-detail",
    ),

    # Insurance Policies (nested under patient)
    path(
        "<uuid:patient_pk>/insurance/",
        views.InsurancePolicyListView.as_view(),
        name="insurance-list",
    ),
    path(
        "insurance/<uuid:pk>/",
        views.InsurancePolicyDetailView.as_view(),
        name="insurance-detail",
    ),

    # Emergency Contacts (nested under patient)
    path(
        "<uuid:patient_pk>/contacts/",
        views.EmergencyContactListView.as_view(),
        name="emergency-contact-list",
    ),
    path(
        "contacts/<uuid:pk>/",
        views.EmergencyContactDetailView.as_view(),
        name="emergency-contact-detail",
    ),

    # Consent Management (nested under patient)
    path(
        "<uuid:patient_pk>/consents/",
        views.ConsentListView.as_view(),
        name="consent-list",
    ),
    path(
        "consents/<uuid:pk>/withdraw/",
        views.ConsentWithdrawView.as_view(),
        name="consent-withdraw",
    ),
]
