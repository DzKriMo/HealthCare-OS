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
    t = Tenant.objects.create(name="TC", slug="pc")
    for c in ["peds.read","peds.write","patients.read"]:
        Permission.objects.get_or_create(codename=c, defaults={"description":"R","resource":"peds","action":"read"})
    role = Role.objects.create(tenant=t, name="Peds")
    for c in ["peds.read","peds.write","patients.read"]:
        role.permissions.add(Permission.objects.get(codename=c))
    User.objects.create_user(email="p@pc.com", password="pass1234567890", first_name="P", last_name="U", tenant=t, role=role)
    Patient.objects.create(tenant=t, first_name="K", last_name="I", display_id="PK-01", date_of_birth="2020-01-01", phone_primary="+1", address_line1="A", city="X", country="US")
    return t

@pytest.fixture
def api_client(): return APIClient()

@pytest.fixture
def patient(tenant): return Patient.objects.for_tenant(tenant).first()

@pytest.mark.django_db
class TestPeds:
    def test_growth_record(self, api_client, tenant, patient):
        r = api_client.post("/api/auth/login/", {"email":"p@pc.com","password":"pass1234567890","tenant_slug":"pc"}, format="json")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.json()['tokens']['access']}", HTTP_X_TENANT_SLUG="pc")
        resp = api_client.post("/api/peds/growth/", {"patient":str(patient.id),"height_cm":"85.0","weight_kg":"12.5"}, format="json")
        assert resp.status_code == status.HTTP_201_CREATED

    def test_vax_schedule(self, api_client, tenant, patient):
        r = api_client.post("/api/auth/login/", {"email":"p@pc.com","password":"pass1234567890","tenant_slug":"pc"}, format="json")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.json()['tokens']['access']}", HTTP_X_TENANT_SLUG="pc")
        resp = api_client.post("/api/peds/vaccinations/", {"patient":str(patient.id),"vaccine_name":"MMR","recommended_age_months":12}, format="json")
        assert resp.status_code == status.HTTP_201_CREATED

    def test_milestone(self, api_client, tenant, patient):
        r = api_client.post("/api/auth/login/", {"email":"p@pc.com","password":"pass1234567890","tenant_slug":"pc"}, format="json")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.json()['tokens']['access']}", HTTP_X_TENANT_SLUG="pc")
        resp = api_client.post("/api/peds/milestones/", {"patient":str(patient.id),"age_group":"12m","domain":"gross_motor","milestone_name":"Walks independently","is_achieved":True}, format="json")
        assert resp.status_code == status.HTTP_201_CREATED

    def test_dashboard(self, api_client, tenant, patient):
        r = api_client.post("/api/auth/login/", {"email":"p@pc.com","password":"pass1234567890","tenant_slug":"pc"}, format="json")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.json()['tokens']['access']}", HTTP_X_TENANT_SLUG="pc")
        resp = api_client.get("/api/peds/dashboard/")
        assert resp.status_code == status.HTTP_200_OK
