"""Tests for dermatology module."""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from tenancy.models import Tenant
from identity.models import Role, Permission
from patients.models import Patient

User = get_user_model()

@pytest.fixture
def tenant(db):
    t = Tenant.objects.create(name="TC", slug="dc")
    Permission.objects.get_or_create(codename="derm.read", defaults={"description":"R","resource":"derm","action":"read"})
    Permission.objects.get_or_create(codename="derm.write", defaults={"description":"W","resource":"derm","action":"write"})
    Permission.objects.get_or_create(codename="patients.read", defaults={"description":"R","resource":"patients","action":"read"})
    role = Role.objects.create(tenant=t, name="Derm")
    for codename in ["derm.read","derm.write","patients.read"]:
        role.permissions.add(Permission.objects.get(codename=codename))
    User.objects.create_user(email="d@dc.com", password="pass1234567890", first_name="D", last_name="U", tenant=t, role=role)
    Patient.objects.create(tenant=t, first_name="P", last_name="T", display_id="PD-01", date_of_birth="1990-01-01", phone_primary="+1", address_line1="A", city="X", country="US")
    return t

@pytest.fixture
def api_client(): return APIClient()

@pytest.fixture
def patient(tenant): return Patient.objects.for_tenant(tenant).first()

@pytest.mark.django_db
class TestDerm:
    def test_get_body_map(self, api_client, tenant, patient):
        r = api_client.post("/api/auth/login/", {"email":"d@dc.com","password":"pass1234567890","tenant_slug":"dc"}, format="json")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.json()['tokens']['access']}", HTTP_X_TENANT_SLUG="dc")
        resp = api_client.get(f"/api/derm/body-map/{patient.id}/")
        assert resp.status_code == status.HTTP_200_OK

    def test_add_lesion(self, api_client, tenant, patient):
        r = api_client.post("/api/auth/login/", {"email":"d@dc.com","password":"pass1234567890","tenant_slug":"dc"}, format="json")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.json()['tokens']['access']}", HTTP_X_TENANT_SLUG="dc")
        resp = api_client.post(f"/api/derm/lesions/{patient.id}/", {"body_region":"trunk_front","location_detail":"Upper back","size_mm":"5.0","color":"Brown","morphology":"Macule","clinical_impression":"Nevus"}, format="json")
        assert resp.status_code == status.HTTP_201_CREATED

    def test_procedure(self, api_client, tenant, patient):
        r = api_client.post("/api/auth/login/", {"email":"d@dc.com","password":"pass1234567890","tenant_slug":"dc"}, format="json")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.json()['tokens']['access']}", HTTP_X_TENANT_SLUG="dc")
        resp = api_client.post("/api/derm/procedures/", {"patient":str(patient.id),"procedure_type":"biopsy","description":"Punch biopsy"}, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
