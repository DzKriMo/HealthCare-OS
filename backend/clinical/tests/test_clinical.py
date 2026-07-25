"""Tests for clinical module."""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from tenancy.models import Tenant
from identity.models import Role, Permission
from patients.models import Patient

User = get_user_model()

@pytest.fixture
def tenant(): return Tenant.objects.create(name="TC", slug="tc")

@pytest.fixture
def perms():
    for c,d,r,a in [("clinical.read","R","clinical","read"),("clinical.write","W","clinical","write"),
                     ("clinical.diagnose","D","clinical","diagnose"),("clinical.refer","Re","clinical","refer"),
                     ("patients.read","R","patients","read")]:
        Permission.objects.get_or_create(codename=c, defaults={"description":d,"resource":r,"action":a})

@pytest.fixture
def role(tenant, perms):
    r = Role.objects.create(tenant=tenant, name="Doctor")
    r.permissions.add(*Permission.objects.filter(codename__startswith="clinical"))
    r.permissions.add(Permission.objects.get(codename="patients.read"))
    return r

@pytest.fixture
def user(tenant, role):
    return User.objects.create_user(email="doc@t.com", password="pass1234567890", first_name="Doc", last_name="User", tenant=tenant, role=role)

@pytest.fixture
def patient(tenant):
    return Patient.objects.create(tenant=tenant, first_name="P", last_name="T", display_id="P-01", date_of_birth="1990-01-01", phone_primary="+1", address_line1="A", city="X", country="US")

@pytest.fixture
def api_client(): return APIClient()

def _auth(c):
    r = c.post("/api/auth/login/", {"email":"doc@t.com","password":"pass1234567890","tenant_slug":"tc"}, format="json")
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {r.json()['tokens']['access']}", HTTP_X_TENANT_SLUG="tc")

@pytest.mark.django_db
class TestClinical:
    def test_create_encounter(self, api_client, user, patient, tenant):
        _auth(api_client)
        resp = api_client.post("/api/clinical/encounters/", {
            "patient":str(patient.id),"subjective":"Headache x 3 days","objective":"Vitals normal",
            "assessment":"Tension headache","plan":"Rest, hydration, PRN ibuprofen",
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json()["assessment"] == "Tension headache"

    def test_sign_encounter(self, api_client, user, patient, tenant):
        _auth(api_client)
        from clinical.models import Encounter
        enc = Encounter.objects.create(tenant=tenant, patient=patient, practitioner=user, encounter_date="2024-01-01")
        resp = api_client.post(f"/api/clinical/encounters/{enc.id}/sign/")
        assert resp.status_code == status.HTTP_200_OK
        enc.refresh_from_db()
        assert enc.status == "signed"

    def test_record_diagnosis(self, api_client, user, patient, tenant):
        _auth(api_client)
        resp = api_client.post("/api/clinical/diagnoses/", {
            "patient":str(patient.id),"icd_code":"J45.909","description":"Unspecified asthma, uncomplicated",
            "diagnosis_type":"primary",
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED

    def test_create_referral(self, api_client, user, patient, tenant):
        _auth(api_client)
        resp = api_client.post("/api/clinical/referrals/", {
            "patient":str(patient.id),"specialist_name":"Dr. Smith","specialty":"Cardiology",
            "reason":"Persistent hypertension","urgency":"urgent",
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED

    def test_record_vitals(self, api_client, user, patient, tenant):
        _auth(api_client)
        resp = api_client.post("/api/clinical/vitals/", {
            "patient":str(patient.id),"systolic_bp":120,"diastolic_bp":80,"heart_rate":72,
            "height_cm":170,"weight_kg":70,
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
    def test_vaccination(self, api_client, user, patient, tenant):
        _auth(api_client)
        resp = api_client.post("/api/clinical/vaccinations/", {
            "patient":str(patient.id),"vaccine_name":"Influenza","dose_number":1,"administered_date":"2024-10-01",
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED

    def test_history(self, api_client, user, patient, tenant):
        _auth(api_client)
        # Add family history
        resp = api_client.post("/api/clinical/history/", {
            "type":"family","patient_id":str(patient.id),
            "data":{"relationship":"Father","condition":"Hypertension","patient":str(patient.id)},
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED

    def test_dashboard(self, api_client, user, tenant):
        _auth(api_client)
        resp = api_client.get("/api/clinical/dashboard/")
        assert resp.status_code == status.HTTP_200_OK
