import pytest; from django.contrib.auth import get_user_model; from rest_framework.test import APIClient; from rest_framework import status
from tenancy.models import Tenant; from identity.models import Role, Permission; from patients.models import Patient
User = get_user_model()

@pytest.fixture
def tenant(db):
    t = Tenant.objects.create(name="TC", slug="vc")
    for c in ["vet.read","vet.write","patients.read"]: Permission.objects.get_or_create(codename=c, defaults={"description":"R","resource":"vet","action":"read"})
    role = Role.objects.create(tenant=t, name="Vet")
    for c in ["vet.read","vet.write","patients.read"]: role.permissions.add(Permission.objects.get(codename=c))
    User.objects.create_user(email="v@vc.com", password="pass1234567890", first_name="V", last_name="U", tenant=t, role=role)
    Patient.objects.create(tenant=t, first_name="P", last_name="T", display_id="PV", date_of_birth="2020-01-01", phone_primary="+1", address_line1="A", city="X", country="US")
    return t
@pytest.fixture
def api_client(): return APIClient()
@pytest.fixture
def patient(tenant): return Patient.objects.for_tenant(tenant).first()

@pytest.mark.django_db
class TestVet:
    def test_animal_record(self, api_client, tenant, patient):
        r = api_client.post("/api/auth/login/", {"email":"v@vc.com","password":"pass1234567890","tenant_slug":"vc"}, format="json")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.json()['tokens']['access']}", HTTP_X_TENANT_SLUG="vc")
        resp = api_client.get(f"/api/vet/animal/{patient.id}/")
        assert resp.status_code == status.HTTP_200_OK

    def test_rabies_cert(self, api_client, tenant, patient):
        r = api_client.post("/api/auth/login/", {"email":"v@vc.com","password":"pass1234567890","tenant_slug":"vc"}, format="json")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.json()['tokens']['access']}", HTTP_X_TENANT_SLUG="vc")
        resp = api_client.post("/api/vet/rabies/", {"patient":str(patient.id),"vaccine_name":"RabVac","expiration_date":"2027-12-31"}, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
