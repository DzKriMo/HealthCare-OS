"""Tests for payment, calendar, and communication provider configs."""
import pytest; from django.contrib.auth import get_user_model; from rest_framework.test import APIClient; from rest_framework import status
from tenancy.models import Tenant; from identity.models import Role, Permission

User = get_user_model()

@pytest.fixture
def tenant(db):
    t = Tenant.objects.create(name="TC", slug="ic")
    Permission.objects.get_or_create(codename="integrations.manage", defaults={"description":"M","resource":"integrations","action":"manage"})
    role = Role.objects.create(tenant=t, name="Admin")
    role.permissions.add(Permission.objects.get(codename="integrations.manage"))
    User.objects.create_user(email="a@ic.com", password="pass1234567890", first_name="A", last_name="U", tenant=t, role=role)
    return t

@pytest.fixture
def api_client(): return APIClient()

def _auth(c):
    r = c.post("/api/auth/login/", {"email":"a@ic.com","password":"pass1234567890","tenant_slug":"ic"}, format="json")
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {r.json()['tokens']['access']}", HTTP_X_TENANT_SLUG="ic")

@pytest.mark.django_db
class TestProviderConfigs:
    def test_payment_config(self, api_client, tenant):
        _auth(api_client)
        resp = api_client.post("/api/integrations/payment-configs/", {
            "provider":"stripe","is_enabled":True,"is_test_mode":True,"api_key":"sk_test_xxx",
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        resp2 = api_client.get("/api/integrations/payment-configs/")
        assert resp2.status_code == status.HTTP_200_OK
        assert len(resp2.json()) == 1

    def test_calendar_config(self, api_client, tenant):
        _auth(api_client)
        resp = api_client.post("/api/integrations/calendar-configs/", {
            "provider":"google","is_enabled":True,"client_id":"xxx.apps.googleusercontent.com",
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED

    def test_comm_config(self, api_client, tenant):
        _auth(api_client)
        resp = api_client.post("/api/integrations/comm-configs/", {
            "channel":"sms","provider_name":"twilio","is_enabled":True,"from_number":"+1234567890",
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED

    def test_list_all_configs(self, api_client, tenant):
        _auth(api_client)
        api_client.post("/api/integrations/payment-configs/", {"provider":"stripe"}, format="json")
        api_client.post("/api/integrations/calendar-configs/", {"provider":"google"}, format="json")
        api_client.post("/api/integrations/comm-configs/", {"channel":"email","provider_name":"sendgrid"}, format="json")
        assert api_client.get("/api/integrations/payment-configs/").status_code == 200
        assert api_client.get("/api/integrations/calendar-configs/").status_code == 200
        assert api_client.get("/api/integrations/comm-configs/").status_code == 200
