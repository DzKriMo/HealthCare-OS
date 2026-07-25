"""
Tests for patient CRUD, search, and tenant isolation.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from tenancy.models import Tenant
from identity.models import Role, Permission
from patients.models import Patient, Allergy, EmergencyContact, InsurancePolicy, ConsentRecord

User = get_user_model()


@pytest.fixture
def tenant():
    return Tenant.objects.create(name="Test Clinic", slug="test-clinic")


@pytest.fixture
def permission():
    p = Permission.objects.create(codename="patients.read", description="Read patients", resource="patients", action="read")
    p2 = Permission.objects.create(codename="patients.write_demographics", description="Edit patients", resource="patients", action="write_demographics")
    p3 = Permission.objects.create(codename="patients.register", description="Register patients", resource="patients", action="register")
    return p


@pytest.fixture
def role(tenant, permission):
    role = Role.objects.create(tenant=tenant, name="Doctor")
    role.permissions.add(
        Permission.objects.get(codename="patients.read"),
        Permission.objects.get(codename="patients.write_demographics"),
        Permission.objects.get(codename="patients.register"),
    )
    return role


@pytest.fixture
def user(tenant, role):
    return User.objects.create_user(
        email="doctor@test-clinic.com", password="securepassword123",
        first_name="Jane", last_name="Doctor", tenant=tenant, role=role,
    )


@pytest.fixture
def api_client():
    return APIClient()


def _auth(api_client, email="doctor@test-clinic.com", tenant_slug="test-clinic"):
    resp = api_client.post("/api/auth/login/", {
        "email": email, "password": "securepassword123", "tenant_slug": tenant_slug,
    }, format="json")
    tokens = resp.json()["tokens"]
    api_client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {tokens['access']}",
        HTTP_X_TENANT_SLUG=tenant_slug,
    )


# ── Patient CRUD Tests ──────────────────────────────────────

@pytest.mark.django_db
class TestPatientCRUD:
    def test_create_patient(self, api_client, user, tenant):
        """Create a new patient and verify it's tenant-scoped."""
        _auth(api_client)
        response = api_client.post("/api/patients/", {
            "first_name": "Alice", "last_name": "Smith",
            "date_of_birth": "1990-05-15", "gender": "female",
            "phone_primary": "+1234567890", "email": "alice@example.com",
            "address_line1": "123 Main St", "city": "Springfield", "country": "US",
        }, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["first_name"] == "Alice"
        assert data["display_id"].startswith("PAT-")
        assert Patient.objects.filter(tenant=tenant).count() == 1

    def test_list_patients(self, api_client, user, tenant):
        """List patients returns only this tenant's patients."""
        _auth(api_client)

        # Create patient in this tenant
        Patient.objects.create(
            tenant=tenant, first_name="Alice", last_name="Smith",
            date_of_birth="1990-05-15", phone_primary="+123", address_line1="A", city="X", country="US",
        )

        # Create patient in another tenant
        other = Tenant.objects.create(name="Other", slug="other-clinic")
        Patient.objects.create(
            tenant=other, first_name="Bob", last_name="Jones",
            date_of_birth="1985-01-01", phone_primary="+456", address_line1="B", city="Y", country="US",
        )

        response = api_client.get("/api/patients/")
        assert response.status_code == status.HTTP_200_OK
        results = response.json()["results"]
        names = [p["first_name"] for p in results]
        assert "Alice" in names
        assert "Bob" not in names

    def test_get_patient_detail(self, api_client, user, tenant):
        """Patient detail returns full info including related entities."""
        _auth(api_client)
        patient = Patient.objects.create(
            tenant=tenant, first_name="Alice", last_name="Smith",
            date_of_birth="1990-05-15", phone_primary="+123", address_line1="A", city="X", country="US",
        )
        Allergy.objects.create(
            patient=patient, tenant=tenant, substance="Penicillin",
            reaction="Rash", severity="moderate", recorded_by=user,
        )

        response = api_client.get(f"/api/patients/{patient.id}/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["first_name"] == "Alice"
        assert data["full_name"] == "Alice Smith"
        assert len(data["allergies"]) == 1

    def test_update_patient(self, api_client, user, tenant):
        """Update patient demographics."""
        _auth(api_client)
        patient = Patient.objects.create(
            tenant=tenant, first_name="Alice", last_name="Smith",
            date_of_birth="1990-05-15", phone_primary="+123", address_line1="A", city="X", country="US",
        )

        response = api_client.put(f"/api/patients/{patient.id}/", {
            "first_name": "Alicia", "last_name": "Smith",
            "date_of_birth": "1990-05-15", "phone_primary": "+123",
            "address_line1": "456 Oak Ave", "city": "Springfield", "country": "US",
        }, format="json")

        assert response.status_code == status.HTTP_200_OK
        patient.refresh_from_db()
        assert patient.first_name == "Alicia"
        assert patient.address_line1 == "456 Oak Ave"

    def test_archive_patient(self, api_client, user, tenant):
        """Soft-delete (archive) a patient."""
        _auth(api_client)
        patient = Patient.objects.create(
            tenant=tenant, first_name="Alice", last_name="Smith",
            date_of_birth="1990-05-15", phone_primary="+123", address_line1="A", city="X", country="US",
        )

        response = api_client.delete(f"/api/patients/{patient.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        patient.refresh_from_db()
        assert patient.is_active is False

    def test_search_patients(self, api_client, user, tenant):
        """Search finds patients by name."""
        _auth(api_client)
        Patient.objects.create(
            tenant=tenant, first_name="Alice", last_name="Smith",
            display_id="PAT-2024-0001",
            date_of_birth="1990-05-15", phone_primary="+123", address_line1="A", city="X", country="US",
        )
        Patient.objects.create(
            tenant=tenant, first_name="Bob", last_name="Johnson",
            display_id="PAT-2024-0002",
            date_of_birth="1985-01-01", phone_primary="+456", address_line1="B", city="Y", country="US",
        )

        response = api_client.get("/api/patients/?q=Alice")
        assert response.status_code == status.HTTP_200_OK
        results = response.json()["results"]
        assert len(results) == 1
        assert results[0]["first_name"] == "Alice"


# ── Consent Tests ───────────────────────────────────────────

@pytest.mark.django_db
class TestConsent:
    def test_grant_and_withdraw_consent(self, api_client, user, tenant):
        """Grant consent, then withdraw it."""
        _auth(api_client)
        patient = Patient.objects.create(
            tenant=tenant, first_name="Alice", last_name="Smith",
            date_of_birth="1990-05-15", phone_primary="+123", address_line1="A", city="X", country="US",
        )

        # Grant
        resp = api_client.post(f"/api/patients/{patient.id}/consents/", {
            "patient": str(patient.id),
            "consent_type": "treatment",
            "form_name": "General Treatment Consent",
            "form_version": "2.1",
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        consent_id = resp.json()["id"]
        assert resp.json()["status"] == "granted"

        # Withdraw
        resp2 = api_client.post(f"/api/patients/consents/{consent_id}/withdraw/", {
            "reason": "Patient requested withdrawal",
        }, format="json")
        assert resp2.status_code == status.HTTP_200_OK

        # Verify
        consent = ConsentRecord.objects.get(id=consent_id)
        assert consent.status == "withdrawn"


# ── Tenant Isolation Tests ─────────────────────────────────

@pytest.mark.django_db
class TestPatientTenantIsolation:
    def test_cannot_access_other_tenant_patient(self, api_client, user, tenant):
        """Patient from another tenant returns 404."""
        _auth(api_client)
        other = Tenant.objects.create(name="Other", slug="other-clinic")
        patient = Patient.objects.create(
            tenant=other, first_name="Bob", last_name="Secret",
            date_of_birth="1985-01-01", phone_primary="+456", address_line1="B", city="Y", country="US",
        )

        response = api_client.get(f"/api/patients/{patient.id}/")
        assert response.status_code == status.HTTP_404_NOT_FOUND
