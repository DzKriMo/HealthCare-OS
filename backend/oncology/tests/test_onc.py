import pytest; from django.contrib.auth import get_user_model; from rest_framework.test import APIClient; from rest_framework import status
from tenancy.models import Tenant; from identity.models import Role, Permission; from patients.models import Patient
User = get_user_model()

@pytest.fixture
def tenant(db):
    t = Tenant.objects.create(name="TC", slug="oc")
    for c in ["onc.read","onc.write","patients.read"]: Permission.objects.get_or_create(codename=c, defaults={"description":"R","resource":"onc","action":"read"})
    role = Role.objects.create(tenant=t, name="Onc")
    for c in ["onc.read","onc.write","patients.read"]: role.permissions.add(Permission.objects.get(codename=c))
    User.objects.create_user(email="o@oc.com", password="pass1234567890", first_name="O", last_name="U", tenant=t, role=role)
    Patient.objects.create(tenant=t, first_name="P", last_name="T", display_id="PO", date_of_birth="1990-01-01", phone_primary="+1", address_line1="A", city="X", country="US")
    return t
@pytest.fixture
def api_client(): return APIClient()
@pytest.fixture
def patient(tenant): return Patient.objects.for_tenant(tenant).first()

@pytest.mark.django_db
class TestOnc:
    def test_staging(self, api_client, tenant, patient):
        r = api_client.post("/api/auth/login/", {"email":"o@oc.com","password":"pass1234567890","tenant_slug":"oc"}, format="json")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.json()['tokens']['access']}", HTTP_X_TENANT_SLUG="oc")
        resp = api_client.post("/api/onc/staging/", {"patient":str(patient.id),"diagnosis":"Breast Cancer","tnm_t":"T2","tnm_n":"N1","tnm_m":"M0","stage":"II"}, format="json")
        assert resp.status_code == status.HTTP_201_CREATED

    def test_marker(self, api_client, tenant, patient):
        r = api_client.post("/api/auth/login/", {"email":"o@oc.com","password":"pass1234567890","tenant_slug":"oc"}, format="json")
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {r.json()['tokens']['access']}", HTTP_X_TENANT_SLUG="oc")
        resp = api_client.post("/api/onc/markers/", {"patient":str(patient.id),"marker_name":"CA 15-3","value":"25.0","unit":"U/mL"}, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
