import pytest; from django.contrib.auth import get_user_model; from rest_framework.test import APIClient; from rest_framework import status
from tenancy.models import Tenant; from identity.models import Role, Permission; from patients.models import Patient
User = get_user_model()

def _setup(db, slug, perms_list, email_prefix):
    t = Tenant.objects.create(name="TC", slug=slug)
    for c in perms_list: Permission.objects.get_or_create(codename=c, defaults={"description":"R","resource":c.split(".")[0],"action":"read"})
    role = Role.objects.create(tenant=t, name="User")
    for c in perms_list: role.permissions.add(Permission.objects.get(codename=c))
    User.objects.create_user(email=f"{email_prefix}@{slug}.com", password="pass1234567890", first_name="U", last_name="U", tenant=t, role=role)
    Patient.objects.create(tenant=t, first_name="P", last_name="T", display_id=f"P-{slug}", date_of_birth="1990-01-01", phone_primary="+1", address_line1="A", city="X", country="US")
    return t

@pytest.fixture
def tenant(db): return _setup(db, "pc", ["physio.read","physio.write","patients.read"], "p")
@pytest.fixture
def api_client(): return APIClient()
@pytest.fixture
def patient(tenant): return Patient.objects.for_tenant(tenant).first()

@pytest.mark.django_db
class TestPhysio:
    def test_session(self, api_client, tenant, patient):
        r = api_client.post("/api/auth/login/", {"email":"p@pc.com","password":"pass1234567890","tenant_slug":"pc"}, format="json")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.json()['tokens']['access']}", HTTP_X_TENANT_SLUG="pc")
        resp = api_client.post("/api/physio/sessions/", {"patient":str(patient.id),"treatment_type":"Manual Therapy","pain_pre":7}, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
