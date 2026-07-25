"""Tests for API keys, webhooks, and booking self-service."""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from tenancy.models import Tenant
from identity.models import Role, Permission
from identity.apikey import ApiKey
from integrations.models import WebhookEndpoint

User = get_user_model()

@pytest.fixture
def tenant():
    return Tenant.objects.create(name="TC", slug="tc")

@pytest.fixture
def perms():
    Permission.objects.get_or_create(codename="integrations.manage", defaults={"description":"M","resource":"integrations","action":"manage"})

@pytest.fixture
def role(tenant, perms):
    r = Role.objects.create(tenant=tenant, name="Admin")
    r.permissions.add(Permission.objects.get(codename="integrations.manage"))
    return r

@pytest.fixture
def user(tenant, role):
    return User.objects.create_user(email="a@t.com", password="pass1234567890", first_name="A", last_name="U", tenant=tenant, role=role)

@pytest.fixture
def api_client():
    return APIClient()

def _auth(c):
    r = c.post("/api/auth/login/", {"email":"a@t.com","password":"pass1234567890","tenant_slug":"tc"}, format="json")
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {r.json()['tokens']['access']}", HTTP_X_TENANT_SLUG="tc")

@pytest.mark.django_db
class TestApiKeys:
    def test_create_api_key(self, api_client, user, tenant):
        _auth(api_client)
        resp = api_client.post("/api/integrations/api-keys/", {
            "name": "Mobile App", "scopes": ["patients.read", "appointments.create"],
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert "key" in resp.json()
        assert resp.json()["prefix"].startswith("hcos_")

    def test_list_api_keys(self, api_client, user, tenant):
        _auth(api_client)
        ApiKey.generate(tenant=tenant, name="Test Key", scopes=["patients.read"])
        resp = api_client.get("/api/integrations/api-keys/")
        assert resp.status_code == status.HTTP_200_OK

    def test_revoke_api_key(self, api_client, user, tenant):
        _auth(api_client)
        key, _ = ApiKey.generate(tenant=tenant, name="To Revoke", scopes=["patients.read"])
        resp = api_client.post(f"/api/integrations/api-keys/{key.id}/revoke/")
        assert resp.status_code == status.HTTP_200_OK
        key.refresh_from_db()
        assert key.is_active is False

@pytest.mark.django_db
class TestWebhooks:
    def test_create_webhook(self, api_client, user, tenant):
        _auth(api_client)
        resp = api_client.post("/api/integrations/webhooks/", {
            "name": "Patient App", "url": "https://example.com/hooks",
            "events": ["appointment.scheduled", "invoice.paid"],
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json()["events"] == ["appointment.scheduled", "invoice.paid"]

    def test_list_webhooks(self, api_client, user, tenant):
        _auth(api_client)
        WebhookEndpoint.objects.create(tenant=tenant, name="Test", url="https://example.com/hook", secret="s3cret", events=["appointment.scheduled"])
        resp = api_client.get("/api/integrations/webhooks/")
        assert resp.status_code == status.HTTP_200_OK

    def test_deactivate_webhook(self, api_client, user, tenant):
        _auth(api_client)
        wh = WebhookEndpoint.objects.create(tenant=tenant, name="Test", url="https://example.com/hook", secret="s3cret", events=["invoice.paid"])
        resp = api_client.delete(f"/api/integrations/webhooks/{wh.id}/")
        assert resp.status_code == status.HTTP_200_OK

@pytest.mark.django_db
class TestBookingSelfService:
    def test_confirm_via_token(self, api_client, tenant):
        from patients.models import Patient
        from scheduling.models import Appointment, BookingToken
        from django.utils import timezone
        import datetime

        # Setup
        practitioner = User.objects.create_user(email="d@t.com", password="p1234567890", first_name="D", last_name="D", tenant=tenant)
        patient = Patient.objects.create(tenant=tenant, first_name="P", last_name="T", display_id="P-01", date_of_birth="1990-01-01", phone_primary="+1", address_line1="A", city="X", country="US")
        now = timezone.now()
        appt = Appointment.objects.create(
            tenant=tenant, patient=patient, practitioner=practitioner,
            start_time=now + datetime.timedelta(days=1),
            end_time=now + datetime.timedelta(days=1, minutes=30),
            type="consultation",
        )
        token = BookingToken.generate(appt, "confirm")

        resp = api_client.post("/api/appointments/self-service/", {
            "token": token.token, "action": "confirm",
        }, format="json")
        assert resp.status_code == status.HTTP_200_OK
        appt.refresh_from_db()
        assert appt.status == Appointment.Status.CONFIRMED
