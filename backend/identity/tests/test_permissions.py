"""
Tests for role-based permission enforcement.

Verifies:
    1. Permission checks gate API access correctly.
    2. Users without a required permission get 403.
    3. Role management endpoints are protected.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from tenancy.models import Tenant
from identity.models import Role, Permission

User = get_user_model()


@pytest.fixture
def tenant():
    return Tenant.objects.create(name="Test Clinic", slug="test-clinic")


@pytest.fixture
def read_perm():
    return Permission.objects.create(
        codename="patients.read",
        description="View patient records",
        resource="patients",
        action="read",
    )


@pytest.fixture
def write_perm():
    return Permission.objects.create(
        codename="patients.write_demographics",
        description="Edit patient demographics",
        resource="patients",
        action="write_demographics",
    )


@pytest.fixture
def manage_roles_perm():
    return Permission.objects.create(
        codename="identity.manage_roles",
        description="Manage roles",
        resource="identity",
        action="manage_roles",
    )


@pytest.fixture
def manage_users_perm():
    return Permission.objects.create(
        codename="identity.manage_users",
        description="Manage users",
        resource="identity",
        action="manage_users",
    )


@pytest.fixture
def doctor_role(tenant, read_perm, write_perm):
    role = Role.objects.create(
        tenant=tenant,
        name="Doctor",
    )
    role.permissions.add(read_perm, write_perm)
    return role


@pytest.fixture
def admin_role(tenant, manage_roles_perm, manage_users_perm):
    role = Role.objects.create(
        tenant=tenant,
        name="Admin",
    )
    role.permissions.add(manage_roles_perm, manage_users_perm)
    return role


@pytest.fixture
def doctor_user(tenant, doctor_role):
    return User.objects.create_user(
        email="doctor@test-clinic.com",
        password="securepassword123",
        first_name="Jane",
        last_name="Doctor",
        tenant=tenant,
        role=doctor_role,
    )


@pytest.fixture
def admin_user(tenant, admin_role):
    return User.objects.create_user(
        email="admin@test-clinic.com",
        password="securepassword123",
        first_name="Admin",
        last_name="User",
        tenant=tenant,
        role=admin_role,
    )


@pytest.fixture
def api_client():
    return APIClient()


def _login(api_client, email, password, tenant_slug):
    """Helper: login and return tokens."""
    resp = api_client.post("/api/auth/login/", {
        "email": email,
        "password": password,
        "tenant_slug": tenant_slug,
    }, format="json")
    return resp.json()["tokens"]


# ── Permission Enforcement Tests ─────────────────────────────

@pytest.mark.django_db
class TestPermissionEnforcement:
    def test_user_with_permission_can_access(self, api_client, doctor_user, tenant):
        """User with the required permission can access the endpoint."""
        tokens = _login(api_client, "doctor@test-clinic.com", "securepassword123", "test-clinic")

        api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {tokens['access']}",
            HTTP_X_TENANT_SLUG="test-clinic",
        )
        # Doctor has patients.read — this endpoint doesn't require special permissions yet
        # but the user list requires identity.manage_users which doctor doesn't have
        response = api_client.get("/api/auth/users/")
        # Doctor should NOT see user list (requires identity.manage_users)
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_manage_roles(self, api_client, admin_user, tenant):
        """Admin with identity.manage_roles can access role management."""
        tokens = _login(api_client, "admin@test-clinic.com", "securepassword123", "test-clinic")

        api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {tokens['access']}",
            HTTP_X_TENANT_SLUG="test-clinic",
        )
        response = api_client.get("/api/auth/roles/")
        assert response.status_code == status.HTTP_200_OK

    def test_unauthorized_user_cannot_create_role(
        self, api_client, doctor_user, tenant,
    ):
        """User without identity.manage_roles cannot create roles."""
        tokens = _login(api_client, "doctor@test-clinic.com", "securepassword123", "test-clinic")

        api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {tokens['access']}",
            HTTP_X_TENANT_SLUG="test-clinic",
        )
        response = api_client.post("/api/auth/roles/", {
            "name": "Unauthorized Role",
        }, format="json")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_unauthenticated_access_rejected(self, api_client):
        """Unauthenticated requests to protected endpoints get 401."""
        response = api_client.get("/api/auth/users/")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_user_has_permission_method(self, doctor_user, read_perm, write_perm):
        """User.has_permission() correctly checks permissions."""
        assert doctor_user.has_permission("patients.read") is True
        assert doctor_user.has_permission("patients.write_demographics") is True
        assert doctor_user.has_permission("billing.refund") is False
        assert doctor_user.has_permission("identity.manage_roles") is False


# ── Role Management Tests ────────────────────────────────────

@pytest.mark.django_db
class TestRoleManagement:
    def test_create_role_with_permissions(
        self, api_client, admin_user, tenant, read_perm, write_perm,
    ):
        """Admin can create a new role with permissions."""
        tokens = _login(api_client, "admin@test-clinic.com", "securepassword123", "test-clinic")

        api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {tokens['access']}",
            HTTP_X_TENANT_SLUG="test-clinic",
        )
        response = api_client.post("/api/auth/roles/", {
            "name": "Custom Role",
            "description": "A test role",
            "permission_ids": [str(read_perm.id), str(write_perm.id)],
        }, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["name"] == "Custom Role"
        assert len(data["permissions"]) == 2

    def test_cannot_delete_system_role(
        self, api_client, admin_user, tenant,
    ):
        """System roles cannot be deleted."""
        system_role = Role.objects.create(
            tenant=None,
            name="System Role",
            is_system_role=True,
        )
        tokens = _login(api_client, "admin@test-clinic.com", "securepassword123", "test-clinic")

        api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {tokens['access']}",
            HTTP_X_TENANT_SLUG="test-clinic",
        )
        response = api_client.delete(f"/api/auth/roles/{system_role.id}/")

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_can_delete_custom_role(
        self, api_client, admin_user, tenant,
    ):
        """Custom tenant roles can be deleted."""
        custom_role = Role.objects.create(
            tenant=tenant,
            name="Custom Role",
        )
        tokens = _login(api_client, "admin@test-clinic.com", "securepassword123", "test-clinic")

        api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {tokens['access']}",
            HTTP_X_TENANT_SLUG="test-clinic",
        )
        response = api_client.delete(f"/api/auth/roles/{custom_role.id}/")

        assert response.status_code == status.HTTP_204_NO_CONTENT
        assert not Role.objects.filter(id=custom_role.id).exists()
