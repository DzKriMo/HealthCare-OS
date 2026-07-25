from django.urls import path
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
]
