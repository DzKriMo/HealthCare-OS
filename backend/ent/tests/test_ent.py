import pytest; from django.contrib.auth import get_user_model; from rest_framework.test import APIClient; from rest_framework import status
from tenancy.models import Tenant; from identity.models import Role, Permission; from patients.models import Patient
User = get_user_model()

@pytest.fixture
def tenant(db):
    t = Tenant.objects.create(name="TC", slug="ec")
    for c in ["ent.read","ent.write","patients.read"]:
        Permission.objects.get_or_create(codename=c, defaults={"description":"R","resource":"ent","action":"read"})
    role = Role.objects.create(tenant=t, name="ENT")
    for c in ["ent.read","ent.write","patients.read"]: role.permissions.add(Permission.objects.get(codename=c))
    User.objects.create_user(email="e@ec.com", password="pass1234567890", first_name="E", last_name="U", tenant=t, role=role)
    Patient.objects.create(tenant=t, first_name="P", last_name="T", display_id="PE-01", date_of_birth="1990-01-01", phone_primary="+1", address_line1="A", city="X", country="US")
    return t
@pytest.fixture
def api_client(): return APIClient()
@pytest.fixture
def patient(tenant): return Patient.objects.for_tenant(tenant).first()

@pytest.mark.django_db
class TestENT:
    def test_audiology(self, api_client, tenant, patient):
        r = api_client.post("/api/auth/login/", {"email":"e@ec.com","password":"pass1234567890","tenant_slug":"ec"}, format="json")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.json()['tokens']['access']}", HTTP_X_TENANT_SLUG="ec")
        resp = api_client.post("/api/ent/audiology/", {"patient":str(patient.id),"test_type":"pure_tone","hearing_loss_type":"normal"}, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
