from django.urls import path, re_path
from . import views

app_name = "fhir"

urlpatterns = [
    path("metadata", views.FHIRMetadataView.as_view(), name="fhir-metadata"),
    path("Patient", views.FHIRPatientView.as_view(), name="fhir-patient-search"),
    path("Patient/<uuid:pk>", views.FHIRPatientView.as_view(), name="fhir-patient"),
    path("Observation", views.FHIRObservationView.as_view(), name="fhir-observation"),
    path("Encounter", views.FHIREncounterView.as_view(), name="fhir-encounter-search"),
    path("Encounter/<uuid:pk>", views.FHIREncounterView.as_view(), name="fhir-encounter"),
    path("MedicationRequest", views.FHIRMedicationRequestView.as_view(), name="fhir-medication-search"),
    path("MedicationRequest/<uuid:pk>", views.FHIRMedicationRequestView.as_view(), name="fhir-medication"),
    path("AllergyIntolerance", views.FHIRAllergyIntoleranceView.as_view(), name="fhir-allergy-search"),
    path("AllergyIntolerance/<uuid:pk>", views.FHIRAllergyIntoleranceView.as_view(), name="fhir-allergy"),
    path("Condition", views.FHIRConditionView.as_view(), name="fhir-condition-search"),
    path("Condition/<uuid:pk>", views.FHIRConditionView.as_view(), name="fhir-condition"),
    path("Immunization", views.FHIRImmunizationView.as_view(), name="fhir-immunization-search"),
    path("Immunization/<uuid:pk>", views.FHIRImmunizationView.as_view(), name="fhir-immunization"),
    path("Practitioner", views.FHIRPractitionerView.as_view(), name="fhir-practitioner-search"),
    path("Practitioner/<uuid:pk>", views.FHIRPractitionerView.as_view(), name="fhir-practitioner"),
    path("Coverage", views.FHIRCoverageView.as_view(), name="fhir-coverage-search"),
    path("Coverage/<uuid:pk>", views.FHIRCoverageView.as_view(), name="fhir-coverage"),
    path("DiagnosticReport", views.FHIRDiagnosticReportView.as_view(), name="fhir-diagnostic-report-search"),
    path("DiagnosticReport/<uuid:pk>", views.FHIRDiagnosticReportView.as_view(), name="fhir-diagnostic-report"),
    path("Medication", views.FHIRMedicationView.as_view(), name="fhir-medication-search"),
    path("Medication/<uuid:pk>", views.FHIRMedicationView.as_view(), name="fhir-medication"),
]
