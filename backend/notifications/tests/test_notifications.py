"""Tests for notification templates, send, and events."""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from tenancy.models import Tenant
from identity.models import Role, Permission
from notifications.models import NotificationTemplate, NotificationEvent, NotificationChannelConfig

User = get_user_model()

@pytest.fixture
def tenant():
    return Tenant.objects.create(name="Test Clinic", slug="test-clinic")

@pytest.fixture
def perms():
    for c, d, r, a in [("notifications.manage_templates","M","notifications","manage_templates"),("notifications.send","S","notifications","send")]:
        Permission.objects.get_or_create(codename=c, defaults={"description":d,"resource":r,"action":a})

@pytest.fixture
def role(tenant, perms):
    r = Role.objects.create(tenant=tenant, name="Manager")
    r.permissions.add(*Permission.objects.filter(codename__startswith="notifications"))
    return r

@pytest.fixture
def user(tenant, role):
    return User.objects.create_user(email="m@t.com", password="pass1234567890", first_name="M", last_name="U", tenant=tenant, role=role)

@pytest.fixture
def api_client():
    return APIClient()

def _auth(c):
    r = c.post("/api/auth/login/", {"email":"m@t.com","password":"pass1234567890","tenant_slug":"test-clinic"}, format="json")
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {r.json()['tokens']['access']}", HTTP_X_TENANT_SLUG="test-clinic")

@pytest.mark.django_db
class TestNotifications:
    def test_create_template(self, api_client, user, tenant):
        _auth(api_client)
        resp = api_client.post("/api/notifications/templates/", {
            "name": "Appointment Reminder",
            "event_type": "appointment_reminder",
            "channel": "email",
            "subject": "Reminder: {{ patient_name }}",
            "body_text": "Your appointment is at {{ appointment_time }}.",
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json()["event_type"] == "appointment_reminder"

    def test_template_rendering(self, tenant):
        template = NotificationTemplate.objects.create(
            tenant=tenant, name="Test", event_type="appointment_reminder",
            channel="email", subject="Hi {{ patient_name }}",
            body_text="Your appointment: {{ appointment_time }}",
        )
        rendered = template.render({"patient_name": "Alice", "appointment_time": "2:00 PM"})
        assert "Alice" in rendered["subject"]
        assert "2:00 PM" in rendered["body_text"]

    def test_send_notification(self, api_client, user, tenant):
        _auth(api_client)
        resp = api_client.post("/api/notifications/send/", {
            "event_type": "appointment_reminder",
            "channel": "email",
            "recipient_email": "patient@example.com",
            "recipient_name": "Alice Smith",
            "context": {"patient_name": "Alice", "appointment_time": "10:30 AM"},
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json()["status"] == "sent"

    def test_channel_config(self, api_client, user, tenant):
        _auth(api_client)
        resp = api_client.get("/api/notifications/config/")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["email_enabled"] is True
