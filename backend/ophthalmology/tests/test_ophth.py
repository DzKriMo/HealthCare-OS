"""Tests for ophthalmology module."""
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
    t = Tenant.objects.create(name="TC", slug="oc")
    Permission.objects.get_or_create(codename="ophth.read", defaults={"description":"R","resource":"ophth","action":"read"})
    Permission.objects.get_or_create(codename="ophth.write", defaults={"description":"W","resource":"ophth","action":"write"})
    Permission.objects.get_or_create(codename="patients.read", defaults={"description":"R","resource":"patients","action":"read"})
    role = Role.objects.create(tenant=t, name="Ophth")
    for codename in ["ophth.read","ophth.write","patients.read"]:
        role.permissions.add(Permission.objects.get(codename=codename))
    User.objects.create_user(email="o@oc.com", password="pass1234567890", first_name="O", last_name="U", tenant=t, role=role)
    Patient.objects.create(tenant=t, first_name="P", last_name="T", display_id="PO-01", date_of_birth="1990-01-01", phone_primary="+1", address_line1="A", city="X", country="US")
    return t

@pytest.fixture
def api_client(): return APIClient()

@pytest.fixture
def patient(tenant): return Patient.objects.for_tenant(tenant).first()

@pytest.mark.django_db
class TestOphth:
    def test_create_exam(self, api_client, tenant, patient):
        r = api_client.post("/api/auth/login/", {"email":"o@oc.com","password":"pass1234567890","tenant_slug":"oc"}, format="json")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.json()['tokens']['access']}", HTTP_X_TENANT_SLUG="oc")
        resp = api_client.post("/api/ophth/exams/", {
            "patient":str(patient.id),"va_od_best":"20/20","va_os_best":"20/25",
            "iop_od":15,"iop_os":16,"assessment":"Normal exam",
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED

    def test_create_prescription(self, api_client, tenant, patient):
        r = api_client.post("/api/auth/login/", {"email":"o@oc.com","password":"pass1234567890","tenant_slug":"oc"}, format="json")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.json()['tokens']['access']}", HTTP_X_TENANT_SLUG="oc")
        resp = api_client.post("/api/ophth/prescriptions/", {
            "patient":str(patient.id),"prescription_type":"glasses",
            "od_sphere":"-1.25","od_cylinder":"-0.50","od_axis":90,
            "os_sphere":"-1.00","os_cylinder":"-0.25","os_axis":85,"pd":"63.0",
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
