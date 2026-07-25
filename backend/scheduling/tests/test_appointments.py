"""
Tests for appointment CRUD, calendar, conflicts, and status transitions.
"""
import datetime
import pytest
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from tenancy.models import Tenant
from identity.models import Role, Permission
from patients.models import Patient
from scheduling.models import Appointment, PractitionerSchedule, WaitingListEntry, Room

User = get_user_model()


@pytest.fixture
def tenant():
    return Tenant.objects.create(name="Test Clinic", slug="test-clinic")


@pytest.fixture
def perms():
    for codename, desc, resource, action in [
        ("appointments.read", "Read", "appointments", "read"),
        ("appointments.create", "Create", "appointments", "create"),
        ("appointments.edit", "Edit", "appointments", "edit"),
        ("appointments.cancel", "Cancel", "appointments", "cancel"),
        ("patients.read", "Read patients", "patients", "read"),
    ]:
        Permission.objects.get_or_create(codename=codename, defaults={"description": desc, "resource": resource, "action": action})


@pytest.fixture
def role(tenant, perms):
    role = Role.objects.create(tenant=tenant, name="Doctor")
    role.permissions.add(*Permission.objects.filter(codename__startswith="appointments"))
    role.permissions.add(Permission.objects.get(codename="patients.read"))
    return role


@pytest.fixture
def practitioner(tenant, role):
    return User.objects.create_user(
        email="doctor@test-clinic.com", password="securepassword123",
        first_name="Jane", last_name="Doctor", tenant=tenant, role=role,
    )


@pytest.fixture
def patient(tenant):
    return Patient.objects.create(
        tenant=tenant, first_name="Alice", last_name="Smith",
        display_id="PAT-2024-0001",
        date_of_birth="1990-05-15", phone_primary="+123", address_line1="A", city="X", country="US",
    )


@pytest.fixture
def room(tenant):
    return Room.objects.create(tenant=tenant, name="Room 1", color="#0369a1")


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


def _make_appt_time(hour=10, minute=0, days_ahead=1):
    """Create a timezone-aware datetime for an appointment."""
    today = timezone.now().date() + datetime.timedelta(days=days_ahead)
    naive = datetime.datetime.combine(today, datetime.time(hour, minute))
    return timezone.make_aware(naive)


# ── Appointment CRUD ───────────────────────────────────────

@pytest.mark.django_db
class TestAppointmentCRUD:
    def test_create_appointment(self, api_client, practitioner, patient, room, tenant):
        """Create a new appointment."""
        _auth(api_client)
        start = _make_appt_time(10, 0, 1)
        end = _make_appt_time(10, 30, 1)

        response = api_client.post("/api/appointments/", {
            "patient": str(patient.id),
            "practitioner": str(practitioner.id),
            "start_time": start.isoformat(),
            "end_time": end.isoformat(),
            "type": "consultation",
            "room": str(room.id),
        }, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["patient_name"] == "Alice Smith"
        assert data["status"] == "scheduled"

    def test_conflict_detection(self, api_client, practitioner, patient, room, tenant):
        """Creating overlapping appointments is rejected."""
        _auth(api_client)
        start = _make_appt_time(10, 0, 1)
        end = _make_appt_time(10, 30, 1)

        # First appointment
        Appointment.objects.create(
            tenant=tenant, patient=patient, practitioner=practitioner,
            start_time=start, end_time=end, type="consultation",
        )

        # Second overlapping appointment
        response = api_client.post("/api/appointments/", {
            "patient": str(patient.id),
            "practitioner": str(practitioner.id),
            "start_time": _make_appt_time(10, 10, 1).isoformat(),
            "end_time": _make_appt_time(10, 40, 1).isoformat(),
            "type": "consultation",
        }, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "conflict" in str(response.json()).lower()

    def test_list_appointments(self, api_client, practitioner, patient, tenant):
        """List appointments with date filtering."""
        _auth(api_client)
        start = _make_appt_time(10, 0, 1)
        end = _make_appt_time(10, 30, 1)

        Appointment.objects.create(
            tenant=tenant, patient=patient, practitioner=practitioner,
            start_time=start, end_time=end, type="consultation",
        )

        response = api_client.get("/api/appointments/")
        assert response.status_code == status.HTTP_200_OK
        assert len(response.json()["results"]) >= 1

    def test_cancel_appointment(self, api_client, practitioner, patient, tenant):
        """Cancel an appointment via DELETE (soft-cancel)."""
        _auth(api_client)
        start = _make_appt_time(10, 0, 1)
        end = _make_appt_time(10, 30, 1)

        appt = Appointment.objects.create(
            tenant=tenant, patient=patient, practitioner=practitioner,
            start_time=start, end_time=end, type="consultation",
        )

        response = api_client.delete(f"/api/appointments/{appt.id}/")
        assert response.status_code == status.HTTP_204_NO_CONTENT
        appt.refresh_from_db()
        assert appt.status == Appointment.Status.CANCELLED


# ── Status Transitions ─────────────────────────────────────

@pytest.mark.django_db
class TestStatusTransitions:
    def test_valid_transition(self, api_client, practitioner, patient, tenant):
        """Check-in: scheduled → arrived."""
        _auth(api_client)
        start = _make_appt_time(10, 0, 1)
        end = _make_appt_time(10, 30, 1)

        appt = Appointment.objects.create(
            tenant=tenant, patient=patient, practitioner=practitioner,
            start_time=start, end_time=end, type="consultation",
        )

        response = api_client.post(f"/api/appointments/{appt.id}/transition/", {
            "target_status": "arrived",
        }, format="json")

        assert response.status_code == status.HTTP_200_OK
        appt.refresh_from_db()
        assert appt.status == Appointment.Status.ARRIVED
        assert appt.checked_in_at is not None

    def test_invalid_transition(self, api_client, practitioner, patient, tenant):
        """Cannot jump from scheduled to completed."""
        _auth(api_client)
        start = _make_appt_time(10, 0, 1)
        end = _make_appt_time(10, 30, 1)

        appt = Appointment.objects.create(
            tenant=tenant, patient=patient, practitioner=practitioner,
            start_time=start, end_time=end, type="consultation",
        )

        response = api_client.post(f"/api/appointments/{appt.id}/transition/", {
            "target_status": "completed",
        }, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST


# ── Waiting List ───────────────────────────────────────────

@pytest.mark.django_db
class TestWaitingList:
    def test_add_to_waiting_list(self, api_client, practitioner, patient, tenant):
        """Add a patient to the waiting list."""
        _auth(api_client)
        response = api_client.post("/api/appointments/waiting-list/", {
            "patient": str(patient.id),
            "preferred_practitioner": str(practitioner.id),
            "appointment_type": "consultation",
            "priority": "high",
            "reason": "Urgent follow-up needed",
        }, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.json()["priority"] == "high"


# ── Tenant Isolation ───────────────────────────────────────

@pytest.mark.django_db
class TestAppointmentIsolation:
    def test_cannot_see_other_tenant_appointments(self, api_client, practitioner, patient, tenant):
        """Appointments from other tenants are invisible."""
        _auth(api_client)
        other_tenant = Tenant.objects.create(name="Other", slug="other-clinic")
        other_patient = Patient.objects.create(
            tenant=other_tenant, first_name="Bob", last_name="Jones",
            display_id="PAT-2024-0099",
            date_of_birth="1980-01-01", phone_primary="+456", address_line1="B", city="Y", country="US",
        )
        start = _make_appt_time(10, 0, 1)
        end = _make_appt_time(10, 30, 1)

        Appointment.objects.create(
            tenant=other_tenant, patient=other_patient, practitioner=practitioner,
            start_time=start, end_time=end, type="consultation",
        )

        response = api_client.get("/api/appointments/")
        results = response.json()["results"]
        assert len(results) == 0  # None visible in our tenant
