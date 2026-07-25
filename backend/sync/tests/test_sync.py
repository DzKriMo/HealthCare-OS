"""Tests for sync engine — push, pull, conflicts, idempotency."""
import pytest
import uuid
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.test import APIClient
from rest_framework import status
from tenancy.models import Tenant
from identity.models import Role, Permission
from sync.models import DeviceRegistration, SyncOperation, ConflictResolutionRule
from sync.engine import SyncEngine

User = get_user_model()

@pytest.fixture
def tenant():
    return Tenant.objects.create(name="TC", slug="tc")

@pytest.fixture
def perms():
    Permission.objects.get_or_create(codename="sync.access", defaults={"description":"S","resource":"sync","action":"access"})

@pytest.fixture
def role(tenant, perms):
    r = Role.objects.create(tenant=tenant, name="Admin")
    r.permissions.add(Permission.objects.get(codename="sync.access"))
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
class TestDeviceRegistration:
    def test_register_device(self, api_client, user, tenant):
        _auth(api_client)
        resp = api_client.post("/api/sync/devices/register/", {
            "device_name": "Front Desk PC",
            "device_id": str(uuid.uuid4()),
            "platform": "desktop",
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert DeviceRegistration.objects.filter(tenant=tenant).count() == 1

@pytest.mark.django_db
class TestSyncPushPull:
    def test_push_operations(self, api_client, user, tenant):
        _auth(api_client)
        device_id = str(uuid.uuid4())
        SyncEngine.register_device(tenant, "Test Device", device_id)

        resp = api_client.post("/api/sync/push/", {
            "device_id": device_id,
            "operations": [
                {
                    "entity_type": "Patient",
                    "entity_id": str(uuid.uuid4()),
                    "operation_type": "create",
                    "payload": {"first_name": "Alice", "last_name": "Smith"},
                    "base_version": 0,
                    "sequence_number": 1,
                    "idempotency_key": str(uuid.uuid4()),
                    "client_timestamp": timezone.now().isoformat(),
                },
            ],
        }, format="json")

        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert len(data["accepted"]) == 1
        assert data["accepted"][0]["server_version"] == 1

    def test_pull_changes(self, api_client, user, tenant):
        _auth(api_client)
        device_id = str(uuid.uuid4())
        SyncEngine.register_device(tenant, "Test Device", device_id)

        # First push an operation from another device
        other_device = str(uuid.uuid4())
        SyncEngine.register_device(tenant, "Other Device", other_device)
        SyncEngine.push(tenant, other_device, [
            {
                "entity_type": "Patient", "entity_id": str(uuid.uuid4()),
                "operation_type": "create", "payload": {"first_name": "Bob"},
                "base_version": 0, "sequence_number": 1,
                "idempotency_key": str(uuid.uuid4()),
                "client_timestamp": timezone.now().isoformat(),
            },
        ])

        # Now pull from our device
        resp = api_client.post("/api/sync/pull/", {
            "device_id": device_id,
            "since_cursor": "",
        }, format="json")

        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert len(data["changes"]) >= 1

    def test_idempotent_push(self, api_client, user, tenant):
        """Replaying the same operation is safe."""
        _auth(api_client)
        device_id = str(uuid.uuid4())
        SyncEngine.register_device(tenant, "Test Device", device_id)

        idem_key = str(uuid.uuid4())
        op = {
            "entity_type": "Patient", "entity_id": str(uuid.uuid4()),
            "operation_type": "create", "payload": {"first_name": "Alice"},
            "base_version": 0, "sequence_number": 1,
            "idempotency_key": idem_key,
            "client_timestamp": timezone.now().isoformat(),
        }

        # Push twice with same idempotency key
        resp1 = api_client.post("/api/sync/push/", {"device_id": device_id, "operations": [op]}, format="json")
        resp2 = api_client.post("/api/sync/push/", {"device_id": device_id, "operations": [op]}, format="json")

        assert resp1.status_code == status.HTTP_200_OK
        assert resp2.status_code == status.HTTP_200_OK
        # Second push should be marked as duplicate
        assert resp2.json()["accepted"][0].get("duplicate") is True

    def test_sync_status(self, api_client, user, tenant):
        _auth(api_client)
        device_id = str(uuid.uuid4())
        SyncEngine.register_device(tenant, "Test Device", device_id)

        resp = api_client.get(f"/api/sync/status/?device_id={device_id}")
        assert resp.status_code == status.HTTP_200_OK
        assert "pending_count" in resp.json()

@pytest.mark.django_db
class TestConflictRules:
    def test_set_conflict_rule(self, api_client, user, tenant):
        _auth(api_client)
        resp = api_client.post("/api/sync/conflict-rules/", {
            "entity_type": "Encounter",
            "strategy": "manual",
            "merge_safe_fields": ["notes"],
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json()["strategy"] == "manual"

    def test_conflict_detection(self, api_client, user, tenant):
        """Simulate a conflict scenario."""
        _auth(api_client)
        device_a = str(uuid.uuid4())
        device_b = str(uuid.uuid4())
        SyncEngine.register_device(tenant, "Device A", device_a)
        SyncEngine.register_device(tenant, "Device B", device_b)

        entity_id = str(uuid.uuid4())

        # Device A creates a record
        result = SyncEngine.push(tenant, device_a, [
            {
                "entity_type": "Patient", "entity_id": entity_id,
                "operation_type": "create", "payload": {"first_name": "Alice"},
                "base_version": 0, "sequence_number": 1,
                "idempotency_key": str(uuid.uuid4()),
                "client_timestamp": timezone.now().isoformat(),
            },
        ])
        version = result["accepted"][0]["server_version"]

        # Device B tries to update with old base version → conflict
        ConflictResolutionRule.objects.create(
            tenant=tenant, entity_type="Patient",
            strategy=ConflictResolutionRule.Strategy.SERVER_WINS,
        )
        result2 = SyncEngine.push(tenant, device_b, [
            {
                "entity_type": "Patient", "entity_id": entity_id,
                "operation_type": "update", "payload": {"first_name": "Bob"},
                "base_version": 0,  # Stale — should be version
                "sequence_number": 1,
                "idempotency_key": str(uuid.uuid4()),
                "client_timestamp": timezone.now().isoformat(),
            },
        ])

        # Should be conflicted since server_wins strategy
        assert "conflicted" in result2
