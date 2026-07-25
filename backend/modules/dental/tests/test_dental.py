"""Tests for dental module — tooth chart, procedures, plans."""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from tenancy.models import Tenant
from identity.models import Role, Permission
from patients.models import Patient
from modules.dental.models import ToothChart, Tooth, ToothProcedure, DentalTreatmentPlan

User = get_user_model()

@pytest.fixture
def tenant():
    return Tenant.objects.create(name="TC", slug="tc")

@pytest.fixture
def perms():
    perms_data = [
        ("dental.chart.read","R","dental","chart_read"),
        ("dental.chart.write","W","dental","chart_write"),
        ("dental.treatment_plan.read","R","dental","plan_read"),
        ("dental.treatment_plan.write","W","dental","plan_write"),
        ("dental.procedures.read","R","dental","proc_read"),
        ("dental.procedures.perform","W","dental","proc_perform"),
        ("patients.read","R","patients","read"),
    ]
    for c, d, r, a in perms_data:
        Permission.objects.get_or_create(codename=c, defaults={"description":d,"resource":r,"action":a})

@pytest.fixture
def role(tenant, perms):
    r = Role.objects.create(tenant=tenant, name="Dentist")
    r.permissions.add(*Permission.objects.filter(codename__startswith="dental"))
    r.permissions.add(Permission.objects.get(codename="patients.read"))
    return r

@pytest.fixture
def user(tenant, role):
    return User.objects.create_user(email="dds@t.com", password="pass1234567890", first_name="Dentist", last_name="User", tenant=tenant, role=role)

@pytest.fixture
def patient(tenant):
    return Patient.objects.create(tenant=tenant, first_name="A", last_name="S", display_id="P-001", date_of_birth="1990-01-01", phone_primary="+1", address_line1="A", city="X", country="US")

@pytest.fixture
def api_client():
    return APIClient()

def _auth(c):
    r = c.post("/api/auth/login/", {"email":"dds@t.com","password":"pass1234567890","tenant_slug":"tc"}, format="json")
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {r.json()['tokens']['access']}", HTTP_X_TENANT_SLUG="tc")

@pytest.mark.django_db
class TestToothChart:
    def test_get_chart(self, api_client, user, patient, tenant):
        _auth(api_client)
        resp = api_client.get(f"/api/dental/chart/{patient.id}/")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert len(data["teeth"]) == 32  # All permanent teeth initialized
        assert data["teeth"][0]["fdi_number"] == 11

    def test_update_tooth(self, api_client, user, patient, tenant):
        _auth(api_client)
        # First get chart to find a tooth
        resp = api_client.get(f"/api/dental/chart/{patient.id}/")
        tooth = resp.json()["teeth"][0]

        resp2 = api_client.put(f"/api/dental/tooth/{tooth['id']}/", {
            "condition": "decayed",
            "notes": "Mesial caries",
            "surface_data": {"mesial": "decayed"},
        }, format="json")
        assert resp2.status_code == status.HTTP_200_OK
        assert resp2.json()["condition"] == "decayed"

    def test_record_procedure(self, api_client, user, patient, tenant):
        _auth(api_client)
        # Get tooth
        chart_resp = api_client.get(f"/api/dental/chart/{patient.id}/")
        tooth = chart_resp.json()["teeth"][0]

        resp = api_client.post("/api/dental/procedures/", {
            "tooth": tooth["id"],
            "patient": str(patient.id),
            "procedure_type": "filling_composite",
            "surfaces": ["occlusal"],
            "description": "Composite filling on #11",
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json()["procedure_type"] == "filling_composite"
        assert resp.json()["fdi_number"] == 11

@pytest.mark.django_db
class TestTreatmentPlan:
    def test_create_plan(self, api_client, user, patient, tenant):
        _auth(api_client)
        resp = api_client.post("/api/dental/plans/", {
            "patient": str(patient.id),
            "name": "Full Mouth Rehabilitation",
            "notes": "Phase 1: extractions, Phase 2: implants",
            "insurance_estimate": "5000.00",
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json()["name"] == "Full Mouth Rehabilitation"

    def test_list_plans(self, api_client, user, patient, tenant):
        _auth(api_client)
        DentalTreatmentPlan.objects.create(
            tenant=tenant, patient=patient, name="Test Plan",
        )
        resp = api_client.get("/api/dental/plans/")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.json()["results"]) >= 1

    def test_dental_dashboard(self, api_client, user, patient, tenant):
        _auth(api_client)
        resp = api_client.get("/api/dental/dashboard/")
        assert resp.status_code == status.HTTP_200_OK
        assert "today_procedures" in resp.json()
