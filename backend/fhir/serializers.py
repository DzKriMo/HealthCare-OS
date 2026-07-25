"""
FHIR R4 resource serializers — map internal models to FHIR-conformant JSON.

Each serializer produces FHIR R4 compliant output with resourceType,
id, meta, and domain-specific fields.
"""
import uuid
from rest_framework import serializers


class FHIRMeta:
    """FHIR meta/profile constants."""
    PROFILE_PATIENT = "http://hl7.org/fhir/StructureDefinition/Patient"
    PROFILE_OBSERVATION = "http://hl7.org/fhir/StructureDefinition/Observation"
    PROFILE_ENCOUNTER = "http://hl7.org/fhir/StructureDefinition/Encounter"
    PROFILE_MEDICATION_REQUEST = "http://hl7.org/fhir/StructureDefinition/MedicationRequest"


def fhir_id(internal_id) -> str:
    return str(internal_id)


class FHIRPatientSerializer:
    """Convert internal Patient model to FHIR R4 Patient resource."""

    @staticmethod
    def to_fhir(patient) -> dict:
        from patients.models import Patient as P
        return {
            "resourceType": "Patient",
            "id": fhir_id(patient.id),
            "meta": {
                "versionId": "1",
                "lastUpdated": patient.updated_at.isoformat() if patient.updated_at else None,
                "profile": [FHIRMeta.PROFILE_PATIENT],
            },
            "identifier": [
                {"system": "urn:oid:2.16.840.1.113883.3.1", "value": patient.display_id or patient.id},
            ],
            "active": patient.is_active,
            "name": [{
                "use": "official",
                "family": patient.last_name,
                "given": [patient.first_name] + ([patient.middle_name] if patient.middle_name else []),
            }],
            "telecom": [
                {"system": "phone", "value": patient.phone_primary, "use": "home"},
            ] + ([{"system": "email", "value": patient.email}] if patient.email else []),
            "gender": patient.gender if patient.gender != "unknown" else None,
            "birthDate": str(patient.date_of_birth) if patient.date_of_birth else None,
            "address": [{
                "line": [a for a in [patient.address_line1, patient.address_line2] if a],
                "city": patient.city,
                "state": patient.state,
                "postalCode": patient.postal_code,
                "country": patient.country,
            }],
        }


class FHIRObservationSerializer:
    """Convert internal data to FHIR Observation for vitals, labs, etc."""

    @staticmethod
    def from_vitals(vital_signs) -> dict:
        """Convert VitalSigns to FHIR Observation bundle."""
        observations = []
        base = {
            "resourceType": "Observation",
            "status": "final",
            "subject": {"reference": f"Patient/{vital_signs.patient_id}"},
            "effectiveDateTime": vital_signs.recorded_at.isoformat() if vital_signs.recorded_at else None,
        }
        components = [
            ("8480-6", "Systolic BP", "mm[Hg]", vital_signs.systolic_bp),
            ("8462-4", "Diastolic BP", "mm[Hg]", vital_signs.diastolic_bp),
            ("8867-4", "Heart Rate", "/min", vital_signs.heart_rate),
            ("9279-1", "Respiratory Rate", "/min", vital_signs.respiratory_rate),
            ("8310-5", "Body Temperature", "Cel", vital_signs.temperature_c),
            ("2708-6", "O2 Saturation", "%", vital_signs.oxygen_saturation),
            ("8302-2", "Height", "cm", vital_signs.height_cm),
            ("29463-7", "Weight", "kg", vital_signs.weight_kg),
            ("39156-5", "BMI", "kg/m2", vital_signs.bmi),
        ]
        for code, display, unit, value in components:
            if value is not None:
                obs = {**base, "id": str(uuid.uuid4()),
                       "code": {"coding": [{"system":"http://loinc.org","code":code,"display":display}]},
                       "valueQuantity": {"value": float(value),"unit":unit,"system":"http://unitsofmeasure.org","code":unit}}
                observations.append(obs)
        return observations

    @staticmethod
    def from_lab_result(lab_result) -> dict:
        """Convert LabResult to FHIR Observation."""
        return {
            "resourceType": "Observation",
            "id": fhir_id(lab_result.id),
            "status": "final" if lab_result.status == "approved" else "preliminary",
            "category": [{"coding": [{"system":"http://terminology.hl7.org/CodeSystem/observation-category","code":"laboratory"}]}],
            "code": {"coding": [{"system":"http://loinc.org","code":lab_result.test_id,"display":lab_result.test.name}]},
            "subject": {"reference": f"Patient/{lab_result.lab_order.patient_id}"},
            "effectiveDateTime": lab_result.performed_at.isoformat() if lab_result.performed_at else None,
            "valueQuantity": {"value": float(lab_result.value)} if lab_result.value else None,
            "valueString": lab_result.value_text if lab_result.value_text else None,
            "interpretation": [{"coding": [{"system":"http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation","code":lab_result.flag.upper()}]}],
        }


class FHIREncounterSerializer:
    """Convert internal Encounter to FHIR R4 Encounter."""

    @staticmethod
    def to_fhir(encounter) -> dict:
        return {
            "resourceType": "Encounter",
            "id": fhir_id(encounter.id),
            "status": "finished" if encounter.status in ("finalized","signed") else "in-progress",
            "class": {"system":"http://terminology.hl7.org/CodeSystem/v3-ActCode","code":"AMB","display":"ambulatory"},
            "subject": {"reference": f"Patient/{encounter.patient_id}"},
            "participant": [{
                "individual": {"reference": f"Practitioner/{encounter.practitioner_id}"},
            }] if encounter.practitioner_id else [],
            "period": {"start": encounter.created_at.isoformat()},
            "reasonCode": [{"text": encounter.subjective[:200]}] if encounter.subjective else [],
        }


class FHIRMedicationRequestSerializer:
    """Convert internal Prescription to FHIR MedicationRequest."""

    @staticmethod
    def to_fhir(prescription) -> dict:
        return {
            "resourceType": "MedicationRequest",
            "id": fhir_id(prescription.id),
            "status": "active" if prescription.status == "issued" else "completed",
            "intent": "order",
            "medicationCodeableConcept": {"text": f"{prescription.drug_name} {prescription.dosage}"},
            "subject": {"reference": f"Patient/{prescription.patient_id}"},
            "requester": {"reference": f"Practitioner/{prescription.prescribed_by_id}"} if prescription.prescribed_by_id else None,
            "dosageInstruction": [{"text": prescription.frequency,"route": {"text": prescription.route}}] if prescription.frequency else [],
            "dispenseRequest": {
                "quantity": {"value": float(prescription.quantity_prescribed)},
                "numberOfRepeatsAllowed": prescription.refills_authorized,
            } if prescription.quantity_prescribed else None,
        }


class FHIRBundleSerializer:
    """FHIR Bundle for search results and transactions."""

    @staticmethod
    def search_bundle(entries: list, total: int, page: int = 1) -> dict:
        return {
            "resourceType": "Bundle",
            "type": "searchset",
            "total": total,
            "link": [{"relation":"self","url":f"?page={page}"}],
            "entry": [{"fullUrl":f"urn:uuid:{e.get('id','')}","resource":e} for e in entries],
        }
