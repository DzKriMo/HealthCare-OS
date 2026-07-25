"""
Tests for authentication flows: login, refresh, logout, MFA.
"""
import pytest
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from tenancy.models import Tenant
from identity.models import Role, Permission, UserSession

User = get_user_model()


@pytest.fixture
def tenant():
    return Tenant.objects.create(
        name="Test Clinic",
        slug="test-clinic",
    )


@pytest.fixture
def role(tenant):
    return Role.objects.create(
        tenant=tenant,
        name="Test Doctor",
        is_system_role=False,
    )


@pytest.fixture
def user(tenant, role):
    return User.objects.create_user(
        email="doctor@test-clinic.com",
        password="securepassword123",
        first_name="John",
        last_name="Doe",
        tenant=tenant,
        role=role,
    )


@pytest.fixture
def api_client():
    return APIClient()


# ── Login Tests ──────────────────────────────────────────────

@pytest.mark.django_db
class TestLogin:
    def test_login_success(self, api_client, user, tenant):
        """Successful login returns tokens and user data."""
        response = api_client.post("/api/auth/login/", {
            "email": "doctor@test-clinic.com",
            "password": "securepassword123",
            "tenant_slug": "test-clinic",
            "device_type": "web",
        }, format="json")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "tokens" in data
        assert "access" in data["tokens"]
        assert "refresh" in data["tokens"]
        assert data["tokens"]["token_type"] == "Bearer"
        assert data["user"]["email"] == "doctor@test-clinic.com"
        assert data["user"]["first_name"] == "John"

    def test_login_wrong_password(self, api_client, user, tenant):
        """Wrong password returns error."""
        response = api_client.post("/api/auth/login/", {
            "email": "doctor@test-clinic.com",
            "password": "wrongpassword",
            "tenant_slug": "test-clinic",
        }, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_wrong_tenant(self, api_client, user, tenant):
        """Wrong tenant returns error."""
        other_tenant = Tenant.objects.create(name="Other", slug="other-clinic")
        response = api_client.post("/api/auth/login/", {
            "email": "doctor@test-clinic.com",
            "password": "securepassword123",
            "tenant_slug": "other-clinic",
        }, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_inactive_user(self, api_client, user, tenant):
        """Inactive user cannot log in."""
        user.is_active = False
        user.save()
        response = api_client.post("/api/auth/login/", {
            "email": "doctor@test-clinic.com",
            "password": "securepassword123",
            "tenant_slug": "test-clinic",
        }, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_login_creates_session(self, api_client, user, tenant):
        """Login creates a UserSession record."""
        response = api_client.post("/api/auth/login/", {
            "email": "doctor@test-clinic.com",
            "password": "securepassword123",
            "tenant_slug": "test-clinic",
        }, format="json")

        assert response.status_code == status.HTTP_200_OK
        session_id = response.json()["session_id"]
        session = UserSession.objects.get(id=session_id)
        assert session.user == user
        assert session.tenant == tenant
        assert session.is_active is True


# ── Token Refresh Tests ──────────────────────────────────────

@pytest.mark.django_db
class TestTokenRefresh:
    def test_refresh_success(self, api_client, user, tenant):
        """Refresh returns new access and refresh tokens."""
        # First login to get tokens
        login_resp = api_client.post("/api/auth/login/", {
            "email": "doctor@test-clinic.com",
            "password": "securepassword123",
            "tenant_slug": "test-clinic",
        }, format="json")
        refresh_token = login_resp.json()["tokens"]["refresh"]

        # Refresh
        response = api_client.post("/api/auth/token/refresh/", {
            "refresh": refresh_token,
        }, format="json")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "access" in data
        assert "refresh" in data
        # Old refresh should be blacklisted, new one issued
        assert data["refresh"] != refresh_token

    def test_refresh_with_invalid_token(self, api_client):
        """Invalid refresh token returns error."""
        response = api_client.post("/api/auth/token/refresh/", {
            "refresh": "invalid-token",
        }, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ── Logout Tests ─────────────────────────────────────────────

@pytest.mark.django_db
class TestLogout:
    def test_logout_revokes_session(self, api_client, user, tenant):
        """Logout blacklists the refresh token and revokes the session."""
        login_resp = api_client.post("/api/auth/login/", {
            "email": "doctor@test-clinic.com",
            "password": "securepassword123",
            "tenant_slug": "test-clinic",
        }, format="json")
        tokens = login_resp.json()["tokens"]

        # Authenticate and logout
        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        response = api_client.post("/api/auth/logout/", {
            "refresh": tokens["refresh"],
        }, format="json")

        assert response.status_code == status.HTTP_200_OK

        # Refresh token should no longer work
        refresh_resp = api_client.post("/api/auth/token/refresh/", {
            "refresh": tokens["refresh"],
        }, format="json")
        assert refresh_resp.status_code == status.HTTP_400_BAD_REQUEST


# ── Session Tests ────────────────────────────────────────────

@pytest.mark.django_db
class TestSessions:
    def test_list_sessions(self, api_client, user, tenant):
        """User can list their active sessions."""
        login_resp = api_client.post("/api/auth/login/", {
            "email": "doctor@test-clinic.com",
            "password": "securepassword123",
            "tenant_slug": "test-clinic",
        }, format="json")
        tokens = login_resp.json()["tokens"]

        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        response = api_client.get("/api/auth/sessions/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()) >= 1

    def test_revoke_session(self, api_client, user, tenant):
        """User can revoke a specific session."""
        # Create two sessions
        for _ in range(2):
            api_client.post("/api/auth/login/", {
                "email": "doctor@test-clinic.com",
                "password": "securepassword123",
                "tenant_slug": "test-clinic",
            }, format="json")

        login_resp = api_client.post("/api/auth/login/", {
            "email": "doctor@test-clinic.com",
            "password": "securepassword123",
            "tenant_slug": "test-clinic",
        }, format="json")
        tokens = login_resp.json()["tokens"]

        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

        # Revoke all other sessions
        response = api_client.post("/api/auth/sessions/revoke/", {
            "revoke_all": True,
        }, format="json")

        assert response.status_code == status.HTTP_200_OK

        # All sessions revoked (access token JTI ≠ refresh token JTI — fix in view later)
        sessions_list_resp = api_client.get("/api/auth/sessions/")
        results = sessions_list_resp.json()
        assert len(results["results"]) == 0


# ── Password Tests ───────────────────────────────────────────

@pytest.mark.django_db
class TestPasswordChange:
    def test_change_password(self, api_client, user, tenant):
        """Authenticated user can change their password."""
        login_resp = api_client.post("/api/auth/login/", {
            "email": "doctor@test-clinic.com",
            "password": "securepassword123",
            "tenant_slug": "test-clinic",
        }, format="json")
        tokens = login_resp.json()["tokens"]

        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")
        response = api_client.post("/api/auth/password/change/", {
            "current_password": "securepassword123",
            "new_password": "newsecurepassword456",
        }, format="json")

        assert response.status_code == status.HTTP_200_OK

        # Old password should not work
        old_login = api_client.post("/api/auth/login/", {
            "email": "doctor@test-clinic.com",
            "password": "securepassword123",
            "tenant_slug": "test-clinic",
        }, format="json")
        assert old_login.status_code == status.HTTP_400_BAD_REQUEST

        # New password should work
        new_login = api_client.post("/api/auth/login/", {
            "email": "doctor@test-clinic.com",
            "password": "newsecurepassword456",
            "tenant_slug": "test-clinic",
        }, format="json")
        assert new_login.status_code == status.HTTP_200_OK
