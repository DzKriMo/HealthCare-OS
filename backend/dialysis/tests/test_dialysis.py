import pytest; from django.contrib.auth import get_user_model; from rest_framework.test import APIClient; from rest_framework import status
from tenancy.models import Tenant; from identity.models import Role, Permission; from patients.models import Patient
User = get_user_model()

@pytest.fixture
def tenant(db):
    t = Tenant.objects.create(name="TC", slug="dc")
    for c in ["dialysis.read","dialysis.write","patients.read"]: Permission.objects.get_or_create(codename=c, defaults={"description":"R","resource":"dialysis","action":"read"})
    role = Role.objects.create(tenant=t, name="Dial")
    for c in ["dialysis.read","dialysis.write","patients.read"]: role.permissions.add(Permission.objects.get(codename=c))
    User.objects.create_user(email="d@dc.com", password="pass1234567890", first_name="D", last_name="U", tenant=t, role=role)
    Patient.objects.create(tenant=t, first_name="P", last_name="T", display_id="PD", date_of_birth="1990-01-01", phone_primary="+1", address_line1="A", city="X", country="US")
    return t
@pytest.fixture
def api_client(): return APIClient()
@pytest.fixture
def patient(tenant): return Patient.objects.for_tenant(tenant).first()

@pytest.mark.django_db
class TestDialysis:
    def test_session(self, api_client, tenant, patient):
        r = api_client.post("/api/auth/login/", {"email":"d@dc.com","password":"pass1234567890","tenant_slug":"dc"}, format="json")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.json()['tokens']['access']}", HTTP_X_TENANT_SLUG="dc")
        resp = api_client.post("/api/dialysis/sessions/", {"patient":str(patient.id),"dialysis_type":"hemodialysis","pre_weight_kg":"80.0","fluid_removed_ml":2500}, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
