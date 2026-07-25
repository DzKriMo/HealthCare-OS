"""
Tests for billing: items, invoices, payments, POS, revenue.
"""
import decimal
import pytest
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from tenancy.models import Tenant
from identity.models import Role, Permission
from patients.models import Patient
from billing.models import BillingItem, Invoice, Payment, Quote

User = get_user_model()


@pytest.fixture
def tenant():
    return Tenant.objects.create(name="Test Clinic", slug="test-clinic")


@pytest.fixture
def perms():
    for codename, desc, resource, action in [
        ("billing.read", "Read", "billing", "read"),
        ("billing.create_invoice", "Create invoice", "billing", "create_invoice"),
        ("billing.process_payment", "Process payment", "billing", "process_payment"),
        ("billing.refund", "Refund", "billing", "refund"),
        ("billing.manage_items", "Manage items", "billing", "manage_items"),
        ("billing.view_finance", "View finance", "billing", "view_finance"),
        ("patients.read", "Read patients", "patients", "read"),
    ]:
        Permission.objects.get_or_create(codename=codename, defaults={"description": desc, "resource": resource, "action": action})


@pytest.fixture
def role(tenant, perms):
    role = Role.objects.create(tenant=tenant, name="Manager")
    role.permissions.add(*Permission.objects.filter(codename__startswith="billing"))
    role.permissions.add(Permission.objects.get(codename="patients.read"))
    return role


@pytest.fixture
def user(tenant, role):
    return User.objects.create_user(
        email="manager@test-clinic.com", password="securepassword123",
        first_name="Manager", last_name="User", tenant=tenant, role=role,
    )


@pytest.fixture
def patient(tenant):
    return Patient.objects.create(
        tenant=tenant, first_name="Alice", last_name="Smith",
        display_id="PAT-2024-0001",
        date_of_birth="1990-05-15", phone_primary="+123", address_line1="A", city="X", country="US",
    )


@pytest.fixture
def api_client():
    return APIClient()


def _auth(api_client, tenant_slug="test-clinic"):
    resp = api_client.post("/api/auth/login/", {
        "email": "manager@test-clinic.com", "password": "securepassword123", "tenant_slug": tenant_slug,
    }, format="json")
    api_client.credentials(
        HTTP_AUTHORIZATION=f"Bearer {resp.json()['tokens']['access']}",
        HTTP_X_TENANT_SLUG=tenant_slug,
    )


# ── Billing Items ──────────────────────────────────────────

@pytest.mark.django_db
class TestBillingItems:
    def test_create_item(self, api_client, user, tenant):
        _auth(api_client)
        resp = api_client.post("/api/billing/items/", {
            "name": "General Consultation",
            "description": "Standard 30-minute consultation",
            "category": "consultation",
            "price": "150.00",
            "tax_rate": "8.50",
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json()["price"] == "150.00"


# ── Invoice Creation & Calculation ─────────────────────────

@pytest.mark.django_db
class TestInvoiceCalculation:
    def test_create_invoice(self, api_client, user, patient, tenant):
        _auth(api_client)
        resp = api_client.post("/api/billing/invoices/", {
            "patient": str(patient.id),
            "line_items": [
                {"description": "Consultation", "quantity": 1, "unit_price": "150.00", "tax_rate": "10.00"},
                {"description": "X-Ray", "quantity": 2, "unit_price": "75.00", "tax_rate": "10.00"},
            ],
            "discount_total": "0",
        }, format="json")

        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        # subtotal = 150 + 150 = 300
        assert data["subtotal"] == "300.00"
        # tax = 10% of 300 = 30
        assert data["tax_total"] == "30.00"
        assert data["grand_total"] == "330.00"
        assert data["invoice_number"].startswith("INV-")

    def test_invoice_with_discount(self, api_client, user, patient, tenant):
        _auth(api_client)
        resp = api_client.post("/api/billing/invoices/", {
            "patient": str(patient.id),
            "line_items": [
                {"description": "Procedure", "quantity": 1, "unit_price": "500.00", "tax_rate": "0"},
            ],
            "discount_total": "50.00",
        }, format="json")

        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert data["subtotal"] == "500.00"
        assert data["discount_total"] == "50.00"
        assert data["grand_total"] == "450.00"


# ── POS Checkout ───────────────────────────────────────────

@pytest.mark.django_db
class TestPOSCheckout:
    def test_pos_checkout(self, api_client, user, patient, tenant):
        _auth(api_client)
        resp = api_client.post("/api/billing/pos/checkout/", {
            "patient_id": str(patient.id),
            "line_items": [
                {"description": "Toothbrush", "quantity": 1, "unit_price": "5.00", "tax_rate": "0"},
            ],
            "payment_method": "cash",
        }, format="json")

        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert "Invoice paid" in data["message"] or data["invoice"]["status"] == "paid"


# ── Payment & Refund ───────────────────────────────────────

@pytest.mark.django_db
class TestPaymentAndRefund:
    def test_record_payment(self, api_client, user, patient, tenant):
        _auth(api_client)
        # Create invoice first
        inv = Invoice.objects.create(
            tenant=tenant, patient=patient,
            invoice_number="INV-2024-00001",
            line_items=[{"description": "Test", "quantity": 1, "unit_price": "100.00", "tax_rate": "0"}],
            subtotal=decimal.Decimal("100"), grand_total=decimal.Decimal("100"),
        )

        resp = api_client.post("/api/billing/payments/", {
            "patient": str(patient.id),
            "amount": "100.00",
            "method": "card",
            "reference": "TXN-123",
            "allocations": [{"invoice_id": str(inv.id), "amount": "100.00"}],
        }, format="json")

        assert resp.status_code == status.HTTP_201_CREATED
        inv.refresh_from_db()
        assert inv.amount_paid == 100

    def test_refund(self, api_client, user, patient, tenant):
        _auth(api_client)
        inv = Invoice.objects.create(
            tenant=tenant, patient=patient,
            invoice_number="INV-2024-00002",
            line_items=[{"description": "Test", "quantity": 1, "unit_price": "200.00", "tax_rate": "0"}],
            subtotal=decimal.Decimal("200"), grand_total=decimal.Decimal("200"), amount_paid=decimal.Decimal("200"),
        )
        payment = Payment.objects.create(
            tenant=tenant, patient=patient, amount=200, method="card",
            allocations=[{"invoice_id": str(inv.id), "amount": "200.00"}],
        )

        resp = api_client.post(f"/api/billing/payments/{payment.id}/refund/", {
            "amount": "200.00",
            "reason": "Service not provided",
        }, format="json")

        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json()["is_refund"] is True


# ── Revenue Dashboard ──────────────────────────────────────

@pytest.mark.django_db
class TestRevenue:
    def test_revenue_summary(self, api_client, user, tenant):
        _auth(api_client)
        resp = api_client.get("/api/billing/revenue/?period=month")
        assert resp.status_code == status.HTTP_200_OK
        assert "total_revenue" in resp.json()
