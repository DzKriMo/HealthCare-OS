"""
Tests for tenant isolation — the most critical security property.

Verifies:
    1. Users from tenant A cannot access tenant B's data.
    2. Tenant middleware resolves correctly.
    3. Permission checks are tenant-scoped.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from tenancy.models import Tenant
from identity.models import Role, Permission

User = get_user_model()


@pytest.fixture
def tenant_a():
    return Tenant.objects.create(name="Clinic A", slug="clinic-a")


@pytest.fixture
def tenant_b():
    return Tenant.objects.create(name="Clinic B", slug="clinic-b")


@pytest.fixture
def role_a(tenant_a):
    role = Role.objects.create(
        tenant=tenant_a,
        name="Doctor A",
    )
    # Grant user management permission
    perm = Permission.objects.create(
        codename="identity.manage_users",
        description="Manage users",
        resource="identity",
        action="manage_users",
    )
    role.permissions.add(perm)
    return role


@pytest.fixture
def role_b(tenant_b):
    return Role.objects.create(
        tenant=tenant_b,
        name="Doctor B",
    )


@pytest.fixture
def user_a(tenant_a, role_a):
    return User.objects.create_user(
        email="doctor@clinic-a.com",
        password="securepassword123",
        first_name="Alice",
        last_name="Doctor",
        tenant=tenant_a,
        role=role_a,
    )


@pytest.fixture
def user_b(tenant_b, role_b):
    return User.objects.create_user(
        email="doctor@clinic-b.com",
        password="securepassword123",
        first_name="Bob",
        last_name="Doctor",
        tenant=tenant_b,
        role=role_b,
    )


@pytest.fixture
def api_client():
    return APIClient()


# ── Tenant Isolation Tests ───────────────────────────────────

@pytest.mark.django_db
class TestTenantIsolation:
    def test_user_cannot_login_to_wrong_tenant(self, api_client, user_a, tenant_b):
        """User from tenant A cannot log in to tenant B."""
        response = api_client.post("/api/auth/login/", {
            "email": "doctor@clinic-a.com",
            "password": "securepassword123",
            "tenant_slug": "clinic-b",
        }, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_user_cannot_see_other_tenant_users(
        self, api_client, user_a, user_b, tenant_a,
    ):
        """User list endpoint only returns users from the current tenant."""
        # Login as user from tenant A
        login_resp = api_client.post("/api/auth/login/", {
            "email": "doctor@clinic-a.com",
            "password": "securepassword123",
            "tenant_slug": "clinic-a",
        }, format="json")
        tokens = login_resp.json()["tokens"]

        # Request users with tenant A context
        api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {tokens['access']}",
            HTTP_X_TENANT_SLUG="clinic-a",
        )
        response = api_client.get("/api/auth/users/")

        assert response.status_code == status.HTTP_200_OK
        users = response.json()
        user_ids = [u["email"] for u in users["results"]]
        assert "doctor@clinic-a.com" in user_ids
        assert "doctor@clinic-b.com" not in user_ids

    def test_cross_tenant_access_rejected(
        self, api_client, user_a, tenant_b,
    ):
        """User from tenant A cannot access tenant B with X-Tenant-Slug header."""
        login_resp = api_client.post("/api/auth/login/", {
            "email": "doctor@clinic-a.com",
            "password": "securepassword123",
            "tenant_slug": "clinic-a",
        }, format="json")
        tokens = login_resp.json()["tokens"]

        # Try to access tenant B's resources
        api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {tokens['access']}",
            HTTP_X_TENANT_SLUG="clinic-b",
        )
        response = api_client.get("/api/auth/users/")

        # Should fail — user does not belong to tenant B
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_super_admin_cross_tenant_access(self, api_client, tenant_a, tenant_b):
        """Super admin can access any tenant."""
        super_admin = User.objects.create_superuser(
            email="admin@platform.com",
            password="adminpassword123",
            first_name="Super",
            last_name="Admin",
            tenant=None,  # No tenant
        )

        login_resp = api_client.post("/api/auth/login/", {
            "email": "admin@platform.com",
            "password": "adminpassword123",
            "tenant_slug": "",
        }, format="json")
        tokens = login_resp.json()["tokens"]

        # Super admin can access any tenant
        api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {tokens['access']}",
            HTTP_X_TENANT_SLUG="clinic-a",
        )
        response = api_client.get("/api/auth/users/")
        assert response.status_code == status.HTTP_200_OK

        # Also clinic B
        api_client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {tokens['access']}",
            HTTP_X_TENANT_SLUG="clinic-b",
        )
        response = api_client.get("/api/auth/users/")
        assert response.status_code == status.HTTP_200_OK
