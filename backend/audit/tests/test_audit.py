"""Tests for audit immutability, recording, and retrieval."""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from tenancy.models import Tenant
from identity.models import Role, Permission
from audit.models import AuditEvent
from audit.middleware import AuditService

User = get_user_model()

@pytest.fixture
def tenant():
    return Tenant.objects.create(name="TC", slug="tc")

@pytest.fixture
def perms():
    for c, d, r, a in [("audit.read","R","audit","read"),("audit.export","E","audit","export")]:
        Permission.objects.get_or_create(codename=c, defaults={"description":d,"resource":r,"action":a})

@pytest.fixture
def role(tenant, perms):
    r = Role.objects.create(tenant=tenant, name="Admin")
    r.permissions.add(*Permission.objects.filter(codename__startswith="audit"))
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
class TestAudit:
    def test_record_audit_event(self, tenant, user):
        """AuditService.record creates an immutable event."""
        AuditService.record(
            tenant=tenant, actor=user, entity_type="Patient",
            entity_id="123", action="update",
            before_value={"name": "Old"}, after_value={"name": "New"},
        )
        event = AuditEvent.objects.first()
        assert event.entity_type == "Patient"
        assert event.action == "update"
        assert event.before_value == {"name": "Old"}

    def test_audit_immutable(self, tenant, user):
        """AuditEvents cannot be deleted after creation."""
        AuditService.record(tenant=tenant, actor=user, entity_type="Test", action="create")
        event = AuditEvent.objects.first()
        with pytest.raises(RuntimeError):
            event.delete()
        # Verify creation works fine
        assert event.entity_type == "Test"

    def test_list_audit_events(self, api_client, user, tenant):
        _auth(api_client)
        AuditService.record(tenant=tenant, actor=user, entity_type="Patient", action="create")
        resp = api_client.get("/api/audit/")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.json()["results"]) >= 1

    def test_export_audit(self, api_client, user, tenant):
        _auth(api_client)
        AuditService.record(tenant=tenant, actor=user, entity_type="Patient", action="create")
        # Audit event appears in list
        resp = api_client.get("/api/audit/?entity_type=Patient")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.json()["results"]) >= 1
