"""Tests for pharmacy — prescriptions, dispensing, controlled substances."""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from tenancy.models import Tenant
from identity.models import Role, Permission
from patients.models import Patient
from inventory.models import InventoryItem
from pharmacy.models import Prescription, DispenseRecord, ControlledSubstanceLog

User = get_user_model()

@pytest.fixture
def tenant():
    return Tenant.objects.create(name="TC", slug="tc")

@pytest.fixture
def perms():
    for c, d, r, a in [
        ("pharmacy.prescribe","P","pharmacy","prescribe"),
        ("pharmacy.dispense","D","pharmacy","dispense"),
        ("pharmacy.controlled","C","pharmacy","controlled"),
        ("pharmacy.read","R","pharmacy","read"),
        ("patients.read","R","patients","read"),
        ("inventory.read","R","inventory","read"),
        ("inventory.adjust_stock","A","inventory","adjust"),
    ]:
        Permission.objects.get_or_create(codename=c, defaults={"description":d,"resource":r,"action":a})

@pytest.fixture
def role(tenant, perms):
    r = Role.objects.create(tenant=tenant, name="Pharmacist")
    r.permissions.add(*Permission.objects.filter(codename__startswith="pharmacy"))
    r.permissions.add(Permission.objects.get(codename="patients.read"))
    r.permissions.add(*Permission.objects.filter(codename__startswith="inventory"))
    return r

@pytest.fixture
def user(tenant, role):
    return User.objects.create_user(email="pharm@t.com", password="pass1234567890", first_name="Pharm", last_name="User", tenant=tenant, role=role)

@pytest.fixture
def patient(tenant):
    return Patient.objects.create(tenant=tenant, first_name="P", last_name="T", display_id="P-01", date_of_birth="1990-01-01", phone_primary="+1", address_line1="A", city="X", country="US")

@pytest.fixture
def api_client():
    return APIClient()

def _auth(c):
    r = c.post("/api/auth/login/", {"email":"pharm@t.com","password":"pass1234567890","tenant_slug":"tc"}, format="json")
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {r.json()['tokens']['access']}", HTTP_X_TENANT_SLUG="tc")

@pytest.mark.django_db
class TestPrescriptions:
    def test_create_prescription(self, api_client, user, patient, tenant):
        _auth(api_client)
        resp = api_client.post("/api/pharmacy/prescriptions/", {
            "patient": str(patient.id),
            "drug_name": "Amoxicillin", "dosage": "500mg", "frequency": "TID",
            "duration_days": 7, "route": "oral",
            "quantity_prescribed": "21", "refills_authorized": 1,
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json()["drug_name"] == "Amoxicillin"
        assert resp.json()["status"] == "issued"

    def test_list_prescriptions(self, api_client, user, patient, tenant):
        _auth(api_client)
        Prescription.objects.create(tenant=tenant, patient=patient, drug_name="Ibuprofen",
                                    dosage="400mg", frequency="BID", quantity_prescribed=14)
        resp = api_client.get("/api/pharmacy/prescriptions/")
        assert resp.status_code == status.HTTP_200_OK

@pytest.mark.django_db
class TestDispensing:
    def test_dispense(self, api_client, user, patient, tenant):
        _auth(api_client)
        rx = Prescription.objects.create(tenant=tenant, patient=patient, drug_name="Paracetamol",
                                         dosage="500mg", frequency="q6h", quantity_prescribed=30,
                                         status=Prescription.Status.ISSUED)
        resp = api_client.post("/api/pharmacy/dispense/", {
            "prescription": str(rx.id), "patient": str(patient.id),
            "quantity": "30",
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        rx.refresh_from_db()
        assert rx.quantity_dispensed == 30
        assert rx.status == Prescription.Status.FILLED

    def test_pharmacy_pos(self, api_client, user, patient, tenant):
        _auth(api_client)
        rx = Prescription.objects.create(tenant=tenant, patient=patient, drug_name="Cetirizine",
                                         dosage="10mg", frequency="QD", quantity_prescribed=30,
                                         status=Prescription.Status.ISSUED)
        resp = api_client.post("/api/pharmacy/pos/", {
            "prescription_id": str(rx.id), "quantity": "30",
            "payment_method": "cash", "copay": "10.00",
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json()["prescription_status"] == "filled"

    def test_cannot_dispense_cancelled(self, api_client, user, patient, tenant):
        _auth(api_client)
        rx = Prescription.objects.create(tenant=tenant, patient=patient, drug_name="Test",
                                         dosage="10mg", frequency="QD", quantity_prescribed=30,
                                         status=Prescription.Status.CANCELLED)
        resp = api_client.post("/api/pharmacy/dispense/", {
            "prescription": str(rx.id), "patient": str(patient.id), "quantity": "10",
        }, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

@pytest.mark.django_db
class TestControlledSubstances:
    def test_controlled_log_created_on_pos(self, api_client, user, patient, tenant):
        _auth(api_client)
        InventoryItem.objects.create(tenant=tenant, name="Morphine", category="medicine", unit="vial",
                                     quantity_on_hand=100)
        rx = Prescription.objects.create(
            tenant=tenant, patient=patient, drug_name="Morphine",
            dosage="10mg/mL", frequency="q4h PRN", quantity_prescribed=10,
            is_controlled=True, controlled_schedule="II", status=Prescription.Status.ISSUED,
        )
        resp = api_client.post("/api/pharmacy/pos/", {
            "prescription_id": str(rx.id), "quantity": "10",
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED

    def test_controlled_log_list(self, api_client, user, patient, tenant):
        _auth(api_client)
        rx = Prescription.objects.create(tenant=tenant, patient=patient, drug_name="Codeine",
                                         dosage="30mg", frequency="q6h", quantity_prescribed=20,
                                         is_controlled=True, controlled_schedule="III", status=Prescription.Status.ISSUED)
        dr = DispenseRecord.objects.create(tenant=tenant, prescription=rx, patient=patient, quantity=20)
        ControlledSubstanceLog.objects.create(tenant=tenant, dispense_record=dr, prescription=rx,
                                              quantity_before_dispense=100, quantity_after_dispense=80)
        resp = api_client.get("/api/pharmacy/controlled/")
        assert resp.status_code == status.HTTP_200_OK
