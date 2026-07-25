import uuid
from typing import Any


FHIR_VERSION = "4.0.1"
PROFILE_PATIENT = "http://hl7.org/fhir/StructureDefinition/Patient"
PROFILE_OBSERVATION = "http://hl7.org/fhir/StructureDefinition/Observation"
PROFILE_ENCOUNTER = "http://hl7.org/fhir/StructureDefinition/Encounter"
PROFILE_MEDICATION_REQUEST = "http://hl7.org/fhir/StructureDefinition/MedicationRequest"
PROFILE_ALLERGY = "http://hl7.org/fhir/StructureDefinition/AllergyIntolerance"
PROFILE_CONDITION = "http://hl7.org/fhir/StructureDefinition/Condition"
PROFILE_IMMUNIZATION = "http://hl7.org/fhir/StructureDefinition/Immunization"
PROFILE_PRACTITIONER = "http://hl7.org/fhir/StructureDefinition/Practitioner"
PROFILE_ORGANIZATION = "http://hl7.org/fhir/StructureDefinition/Organization"
PROFILE_COVERAGE = "http://hl7.org/fhir/StructureDefinition/Coverage"
PROFILE_DIAGNOSTIC_REPORT = "http://hl7.org/fhir/StructureDefinition/DiagnosticReport"
PROFILE_MEDICATION = "http://hl7.org/fhir/StructureDefinition/Medication"


def fhir_id(internal_id) -> str:
    return str(internal_id)


def operation_outcome(severity: str, code: str, diagnostics: str) -> dict:
    return {
        "resourceType": "OperationOutcome",
        "issue": [{"severity": severity, "code": code, "diagnostics": diagnostics}],
    }


def bundle(entries: list, total: int, page: int = 1, type_: str = "searchset") -> dict:
    return {
        "resourceType": "Bundle",
        "type": type_,
        "total": total,
        "link": [{"relation": "self", "url": f"?page={page}"}],
        "entry": [{"fullUrl": f"urn:uuid:{e.get('id', '')}", "resource": e} for e in entries],
    }


class FHIRPatientSerializer:
    @staticmethod
    def to_fhir(patient) -> dict:
        return {
            "resourceType": "Patient",
            "id": fhir_id(patient.id),
            "meta": {"versionId": "1", "lastUpdated": patient.updated_at.isoformat() if patient.updated_at else None, "profile": [PROFILE_PATIENT]},
            "identifier": [{"system": "urn:oid:2.16.840.1.113883.3.1", "value": patient.display_id or str(patient.id)}],
            "active": patient.is_active,
            "name": [{"use": "official", "family": patient.last_name, "given": [patient.first_name] + ([patient.middle_name] if patient.middle_name else [])}],
            "telecom": [{"system": "phone", "value": patient.phone_primary, "use": "home"}] + ([{"system": "email", "value": patient.email}] if patient.email else []),
            "gender": patient.gender if patient.gender != "unknown" else None,
            "birthDate": str(patient.date_of_birth) if patient.date_of_birth else None,
            "address": [{"line": [a for a in [patient.address_line1, patient.address_line2] if a], "city": patient.city, "state": patient.state, "postalCode": patient.postal_code, "country": patient.country}],
            "maritalStatus": {"text": patient.marital_status} if patient.marital_status else None,
            "generalPractitioner": [{"reference": f"Practitioner/{p.id}"} for p in patient.practitioners.all()] if hasattr(patient, "practitioners") else [],
        }

    @staticmethod
    def from_fhir(data: dict, tenant=None) -> dict:
        name = (data.get("name") or [{}])[0]
        telecom = {t.get("system"): t.get("value") for t in (data.get("telecom") or [])}
        address = (data.get("address") or [{}])[0]
        return {
            "first_name": (name.get("given") or [""])[0],
            "last_name": name.get("family", ""),
            "email": telecom.get("email", ""),
            "phone_primary": telecom.get("phone", ""),
            "gender": data.get("gender", "unknown"),
            "date_of_birth": data.get("birthDate"),
            "address_line1": address.get("line", [""])[0] if address.get("line") else "",
            "city": address.get("city", ""),
            "state": address.get("state", ""),
            "postal_code": address.get("postalCode", ""),
            "country": address.get("country", ""),
        }


class FHIRObservationSerializer:
    @staticmethod
    def from_vitals(vital_signs) -> list:
        observations = []
        base = {"resourceType": "Observation", "meta": {"profile": [PROFILE_OBSERVATION]}, "status": "final", "subject": {"reference": f"Patient/{vital_signs.patient_id}"}, "effectiveDateTime": vital_signs.recorded_at.isoformat() if vital_signs.recorded_at else None}
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
                obs = {**base, "id": str(uuid.uuid4()), "code": {"coding": [{"system": "http://loinc.org", "code": code, "display": display}]}, "valueQuantity": {"value": float(value), "unit": unit, "system": "http://unitsofmeasure.org", "code": unit}}
                observations.append(obs)
        return observations

    @staticmethod
    def from_lab_result(lab_result) -> dict:
        return {
            "resourceType": "Observation", "id": fhir_id(lab_result.id), "meta": {"profile": [PROFILE_OBSERVATION]},
            "status": "final" if lab_result.status == "approved" else "preliminary",
            "category": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/observation-category", "code": "laboratory"}]}],
            "code": {"coding": [{"system": "http://loinc.org", "code": lab_result.test_id, "display": lab_result.test.name}]},
            "subject": {"reference": f"Patient/{lab_result.lab_order.patient_id}"},
            "effectiveDateTime": lab_result.performed_at.isoformat() if lab_result.performed_at else None,
            "valueQuantity": {"value": float(lab_result.value)} if lab_result.value else None,
            "valueString": lab_result.value_text if lab_result.value_text else None,
            "interpretation": [{"coding": [{"system": "http://terminology.hl7.org/CodeSystem/v3-ObservationInterpretation", "code": (lab_result.flag or "").upper()}]}] if lab_result.flag else [],
        }


class FHIREncounterSerializer:
    @staticmethod
    def to_fhir(encounter) -> dict:
        return {
            "resourceType": "Encounter", "id": fhir_id(encounter.id), "meta": {"profile": [PROFILE_ENCOUNTER]},
            "status": "finished" if encounter.status in ("finalized", "signed") else "in-progress",
            "class": {"system": "http://terminology.hl7.org/CodeSystem/v3-ActCode", "code": "AMB", "display": "ambulatory"},
            "subject": {"reference": f"Patient/{encounter.patient_id}"},
            "participant": [{"individual": {"reference": f"Practitioner/{encounter.practitioner_id}"}}] if encounter.practitioner_id else [],
            "period": {"start": encounter.created_at.isoformat()},
            "reasonCode": [{"text": encounter.subjective[:200]}] if encounter.subjective else [],
            "diagnosis": [{"condition": {"reference": d.id}} for d in encounter.diagnoses.all()] if hasattr(encounter, "diagnoses") else [],
        }


class FHIRMedicationRequestSerializer:
    @staticmethod
    def to_fhir(prescription) -> dict:
        return {
            "resourceType": "MedicationRequest", "id": fhir_id(prescription.id), "meta": {"profile": [PROFILE_MEDICATION_REQUEST]},
            "status": "active" if prescription.status == "issued" else "completed",
            "intent": "order",
            "medicationCodeableConcept": {"text": f"{prescription.drug_name} {prescription.dosage}"},
            "subject": {"reference": f"Patient/{prescription.patient_id}"},
            "requester": {"reference": f"Practitioner/{prescription.prescribed_by_id}"} if prescription.prescribed_by_id else None,
            "dosageInstruction": [{"text": prescription.frequency, "route": {"text": prescription.route}}] if prescription.frequency else [],
            "dispenseRequest": {"quantity": {"value": float(prescription.quantity_prescribed)}, "numberOfRepeatsAllowed": prescription.refills_authorized} if prescription.quantity_prescribed else None,
        }


class FHIRAllergyIntoleranceSerializer:
    @staticmethod
    def to_fhir(allergy) -> dict:
        return {
            "resourceType": "AllergyIntolerance", "id": fhir_id(allergy.id), "meta": {"profile": [PROFILE_ALLERGY]},
            "clinicalStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/allergyintolerance-clinical", "code": "active"}]},
            "code": {"coding": [{"system": "http://snomed.info/sct", "display": allergy.substance}]},
            "patient": {"reference": f"Patient/{allergy.patient_id}"},
            "reaction": [{"manifestation": [{"text": allergy.reaction}], "severity": allergy.severity}] if allergy.reaction else [],
        }


class FHIRConditionSerializer:
    @staticmethod
    def to_fhir(diagnosis) -> dict:
        return {
            "resourceType": "Condition", "id": fhir_id(diagnosis.id), "meta": {"profile": [PROFILE_CONDITION]},
            "clinicalStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]},
            "code": {"coding": [{"system": "http://hl7.org/fhir/sid/icd-10-cm", "code": diagnosis.icd10_code, "display": diagnosis.name}]} if diagnosis.icd10_code else {"text": diagnosis.name},
            "subject": {"reference": f"Patient/{diagnosis.patient_id}"},
            "recordedDate": diagnosis.created_at.isoformat() if diagnosis.created_at else None,
        }

    @staticmethod
    def from_medical_history(history) -> dict:
        return {
            "resourceType": "Condition", "id": fhir_id(history.id), "meta": {"profile": [PROFILE_CONDITION]},
            "clinicalStatus": {"coding": [{"system": "http://terminology.hl7.org/CodeSystem/condition-clinical", "code": "active"}]},
            "code": {"text": history.condition},
            "subject": {"reference": f"Patient/{history.patient_id}"},
            "recordedDate": history.created_at.isoformat() if history.created_at else None,
        }


class FHIRImmunizationSerializer:
    @staticmethod
    def to_fhir(vaccination) -> dict:
        return {
            "resourceType": "Immunization", "id": fhir_id(vaccination.id), "meta": {"profile": [PROFILE_IMMUNIZATION]},
            "status": "completed",
            "vaccineCode": {"coding": [{"system": "http://hl7.org/fhir/sid/cvx", "display": vaccination.vaccine_name}]},
            "patient": {"reference": f"Patient/{vaccination.patient_id}"},
            "occurrenceDateTime": vaccination.administered_at.isoformat() if vaccination.administered_at else None,
            "lotNumber": vaccination.lot_number or "",
            "doseQuantity": {"value": 1},
        }


class FHIRPractitionerSerializer:
    @staticmethod
    def to_fhir(user) -> dict:
        return {
            "resourceType": "Practitioner", "id": fhir_id(user.id), "meta": {"profile": [PROFILE_PRACTITIONER]},
            "active": user.is_active,
            "name": [{"use": "official", "family": user.last_name, "given": [user.first_name]}],
            "telecom": [{"system": "email", "value": user.email}],
            "qualification": [{"code": {"coding": [{"display": user.specialty}]}}] if user.specialty else [],
            "identifier": [{"system": "urn:oid:2.16.840.1.113883.3.1", "value": user.license_number}] if user.license_number else [],
        }


class FHIRCoverageSerializer:
    @staticmethod
    def to_fhir(policy) -> dict:
        return {
            "resourceType": "Coverage", "id": fhir_id(policy.id), "meta": {"profile": [PROFILE_COVERAGE]},
            "status": "active",
            "beneficiary": {"reference": f"Patient/{policy.patient_id}"},
            "payor": [{"display": policy.provider}],
            "identifier": [{"system": "urn:oid:2.16.840.1.113883.3.1", "value": policy.policy_number}],
            "type": {"coding": [{"display": policy.coverage_type}]},
            "period": {"start": str(policy.start_date)} if policy.start_date else None,
        }


class FHIRDiagnosticReportSerializer:
    @staticmethod
    def to_fhir(lab_order) -> dict:
        return {
            "resourceType": "DiagnosticReport", "id": fhir_id(lab_order.id), "meta": {"profile": [PROFILE_DIAGNOSTIC_REPORT]},
            "status": "final" if lab_order.status == "completed" else "preliminary",
            "code": {"coding": [{"system": "http://loinc.org", "display": lab_order.test_name or "Lab panel"}]},
            "subject": {"reference": f"Patient/{lab_order.patient_id}"},
            "effectiveDateTime": lab_order.created_at.isoformat() if lab_order.created_at else None,
            "result": [{"reference": f"Observation/{r.id}"} for r in lab_order.results.all()] if hasattr(lab_order, "results") else [],
        }


class FHIRMedicationSerializer:
    @staticmethod
    def to_fhir(item) -> dict:
        return {
            "resourceType": "Medication", "id": fhir_id(item.id), "meta": {"profile": [PROFILE_MEDICATION]},
            "code": {"coding": [{"system": "http://www.nlm.nih.gov/research/umls/rxnorm", "display": item.name}]},
            "status": "active" if item.is_active else "inactive",
        }
