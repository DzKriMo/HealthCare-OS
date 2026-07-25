import pytest; from django.contrib.auth import get_user_model; from rest_framework.test import APIClient; from rest_framework import status
from tenancy.models import Tenant; from identity.models import Role, Permission

User = get_user_model()

@pytest.fixture
def tenant(db):
    t = Tenant.objects.create(name="TC", slug="ic2")
    Permission.objects.get_or_create(codename="integrations.manage", defaults={"description":"M","resource":"integrations","action":"manage"})
    role = Role.objects.create(tenant=t, name="Admin")
    role.permissions.add(Permission.objects.get(codename="integrations.manage"))
    User.objects.create_user(email="a@ic2.com", password="pass1234567890", first_name="A", last_name="U", tenant=t, role=role)
    return t

@pytest.fixture
def api_client(): return APIClient()

def _auth(c):
    r = c.post("/api/auth/login/", {"email":"a@ic2.com","password":"pass1234567890","tenant_slug":"ic2"}, format="json")
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {r.json()['tokens']['access']}", HTTP_X_TENANT_SLUG="ic2")

@pytest.mark.django_db
class TestInsurance:
    def test_clearinghouse_config(self, api_client, tenant):
        _auth(api_client)
        resp = api_client.post("/api/integrations/clearinghouses/", {"name":"Availity","is_enabled":True}, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        resp2 = api_client.get("/api/integrations/clearinghouses/")
        assert resp2.status_code == status.HTTP_200_OK

    def test_edi_claim(self, api_client, tenant):
        _auth(api_client)
        resp = api_client.post("/api/integrations/edi-claims/", {"transaction_type":"837P"}, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json()["claim_number"].startswith("EDI-")

    def test_accounting_config(self, api_client, tenant):
        _auth(api_client)
        resp = api_client.post("/api/integrations/accounting/", {"provider":"quickbooks","is_enabled":True}, format="json")
        assert resp.status_code == status.HTTP_201_CREATED

    def test_government_config(self, api_client, tenant):
        _auth(api_client)
        resp = api_client.post("/api/integrations/government/", {"connector_type":"pdmp","is_enabled":True}, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
