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
    t = Tenant.objects.create(name="TC", slug="cc")
    for c in ["cardio.read","cardio.write","patients.read"]:
        Permission.objects.get_or_create(codename=c, defaults={"description":"R","resource":"cardio","action":"read"})
    role = Role.objects.create(tenant=t, name="Cardio")
    for c in ["cardio.read","cardio.write","patients.read"]:
        role.permissions.add(Permission.objects.get(codename=c))
    User.objects.create_user(email="c@cc.com", password="pass1234567890", first_name="C", last_name="U", tenant=t, role=role)
    Patient.objects.create(tenant=t, first_name="P", last_name="T", display_id="PC-01", date_of_birth="1990-01-01", phone_primary="+1", address_line1="A", city="X", country="US")
    return t

@pytest.fixture
def api_client(): return APIClient()

@pytest.fixture
def patient(tenant): return Patient.objects.for_tenant(tenant).first()

@pytest.mark.django_db
class TestCardio:
    def test_record_ecg(self, api_client, tenant, patient):
        r = api_client.post("/api/auth/login/", {"email":"c@cc.com","password":"pass1234567890","tenant_slug":"cc"}, format="json")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.json()['tokens']['access']}", HTTP_X_TENANT_SLUG="cc")
        resp = api_client.post("/api/cardio/ecg/", {"patient":str(patient.id),"rhythm":"Sinus","heart_rate":72,"is_abnormal":False}, format="json")
        assert resp.status_code == status.HTTP_201_CREATED

    def test_bp_reading(self, api_client, tenant, patient):
        r = api_client.post("/api/auth/login/", {"email":"c@cc.com","password":"pass1234567890","tenant_slug":"cc"}, format="json")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.json()['tokens']['access']}", HTTP_X_TENANT_SLUG="cc")
        resp = api_client.post("/api/cardio/bp/", {"patient":str(patient.id),"systolic":120,"diastolic":80,"pulse":72}, format="json")
        assert resp.status_code == status.HTTP_201_CREATED

    def test_dashboard(self, api_client, tenant, patient):
        r = api_client.post("/api/auth/login/", {"email":"c@cc.com","password":"pass1234567890","tenant_slug":"cc"}, format="json")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.json()['tokens']['access']}", HTTP_X_TENANT_SLUG="cc")
        resp = api_client.get("/api/cardio/dashboard/")
        assert resp.status_code == status.HTTP_200_OK
