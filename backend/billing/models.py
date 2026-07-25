"""
Billing and payments models — Sprint 4.

Core entities:
    BillingItem — catalog of billable services, products, packages.
    Quote — pre-invoice estimate, convert to invoice on acceptance.
    Invoice — issued bill with line items, taxes, discounts, status state machine.
    Payment — payment against invoice(s) with method, reference, refund support.
    InsuranceClaim — basic claim tracking against invoices.
"""
import uuid
import decimal
from django.db import models
from django.db.models import Sum, Q
from django.core.exceptions import ValidationError
from django.utils import timezone

from tenancy.models import Tenant
from tenancy.managers import TenantScopedManager
from patients.models import Patient


# ═══════════════════════════════════════════════════════════════
# Billing Item Catalog
# ═══════════════════════════════════════════════════════════════

class BillingItem(models.Model):
    """
    Catalog item — a billable service, product, or package.

    Each item has a base price and optional tax rate. When used in an
    invoice, the price is snapshotted into the line item to preserve
    historical accuracy.
    """

    class Category(models.TextChoices):
        CONSULTATION = "consultation", "Consultation"
        PROCEDURE = "procedure", "Procedure"
        LAB = "lab", "Laboratory"
        IMAGING = "imaging", "Imaging"
        MEDICATION = "medication", "Medication"
        SUPPLIES = "supplies", "Supplies"
        PACKAGE = "package", "Package"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="billing_items")

    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=30, choices=Category.choices)
    price = models.DecimalField(max_digits=12, decimal_places=2)
    tax_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=0.00,
        help_text="Tax rate as percentage, e.g. 8.50 for 8.5%.",
    )
    accounting_code = models.CharField(max_length=50, blank=True)
    is_active = models.BooleanField(default=True)

    # For package items: bundle other items
    is_package = models.BooleanField(default=False)
    package_items = models.ManyToManyField(
        "self", blank=True, symmetrical=False,
        help_text="Items included in this package.",
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "billing_item"
        ordering = ["category", "name"]
        indexes = [
            models.Index(fields=["tenant"]),
            models.Index(fields=["tenant", "category"]),
            models.Index(fields=["tenant", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} — ${self.price}"


# ═══════════════════════════════════════════════════════════════
# Quote
# ═══════════════════════════════════════════════════════════════

class Quote(models.Model):
    """
    Pre-invoice estimate. Can be accepted and converted to an invoice.
    """

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SENT = "sent", "Sent"
        ACCEPTED = "accepted", "Accepted"
        DECLINED = "declined", "Declined"
        EXPIRED = "expired", "Expired"
        CONVERTED = "converted", "Converted to Invoice"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="quotes")
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name="quotes")
    quote_number = models.CharField(max_length=30, db_index=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)

    # Line items stored as JSON for immutability
    # [{ "billing_item_id": ..., "description": ..., "quantity": 1, "unit_price": "100.00", "tax_rate": "8.50" }]
    line_items = models.JSONField(default=list)

    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    notes = models.TextField(blank=True)
    valid_until = models.DateField(null=True, blank=True)

    created_by = models.ForeignKey(
        "identity.User", on_delete=models.PROTECT, null=True, related_name="quotes",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Converted invoice tracking
    converted_invoice = models.OneToOneField(
        "Invoice", on_delete=models.SET_NULL, null=True, blank=True, related_name="source_quote",
    )

    objects = TenantScopedManager()

    class Meta:
        db_table = "billing_quote"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant"]),
            models.Index(fields=["tenant", "patient"]),
            models.Index(fields=["tenant", "status"]),
        ]

    def __str__(self):
        return f"Quote {self.quote_number} — {self.patient.full_name}"

    @classmethod
    def calculate_totals(cls, line_items: list[dict], discount_amount: decimal.Decimal = decimal.Decimal("0")) -> dict:
        """Calculate subtotal, tax, and grand total from line items."""
        subtotal = decimal.Decimal("0")
        tax_total = decimal.Decimal("0")

        for item in line_items:
            qty = decimal.Decimal(str(item.get("quantity", 1)))
            unit_price = decimal.Decimal(str(item.get("unit_price", "0")))
            tax_rate = decimal.Decimal(str(item.get("tax_rate", "0")))
            line_subtotal = qty * unit_price
            subtotal += line_subtotal
            tax_total += line_subtotal * (tax_rate / decimal.Decimal("100"))

        grand_total = subtotal + tax_total - discount_amount

        return {
            "subtotal": subtotal.quantize(decimal.Decimal("0.01")),
            "tax_total": tax_total.quantize(decimal.Decimal("0.01")),
            "discount_total": discount_amount.quantize(decimal.Decimal("0.01")),
            "grand_total": max(grand_total, decimal.Decimal("0")).quantize(decimal.Decimal("0.01")),
        }


# ═══════════════════════════════════════════════════════════════
# Invoice
# ═══════════════════════════════════════════════════════════════

class Invoice(models.Model):
    """
    A bill issued to a patient or insurance payer.

    Status flow: draft → issued → (partially_paid | paid | overdue) → cancelled
    """

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ISSUED = "issued", "Issued"
        PARTIALLY_PAID = "partially_paid", "Partially Paid"
        PAID = "paid", "Paid"
        OVERDUE = "overdue", "Overdue"
        CANCELLED = "cancelled", "Cancelled"
        VOID = "void", "Void"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="invoices")
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name="invoices")
    invoice_number = models.CharField(max_length=30, db_index=True)

    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT, db_index=True)

    # Line items snapshotted from billing items at time of invoice creation
    line_items = models.JSONField(default=list)

    # Financials
    subtotal = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    tax_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    discount_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    grand_total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    balance_due = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Dates
    issued_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    paid_date = models.DateField(null=True, blank=True)

    notes = models.TextField(blank=True)
    internal_notes = models.TextField(blank=True)

    created_by = models.ForeignKey(
        "identity.User", on_delete=models.PROTECT, null=True, related_name="invoices",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "billing_invoice"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant"]),
            models.Index(fields=["tenant", "patient"]),
            models.Index(fields=["tenant", "status"]),
            models.Index(fields=["tenant", "invoice_number"]),
            models.Index(fields=["tenant", "due_date"]),
        ]

    def __str__(self):
        return f"Invoice {self.invoice_number} — {self.patient.full_name}"

    def save(self, *args, **kwargs):
        """Calculate financials before saving."""
        if self.line_items:
            discount = decimal.Decimal(str(self.discount_total or 0))
            totals = Quote.calculate_totals(self.line_items, discount)
            self.subtotal = totals["subtotal"]
            self.tax_total = totals["tax_total"]
            self.grand_total = totals["grand_total"]
        self.balance_due = self.grand_total - self.amount_paid
        super().save(*args, **kwargs)

    @property
    def is_paid(self) -> bool:
        return self.status == self.Status.PAID or self.balance_due <= 0

    def update_payment_status(self):
        """Recalculate payment status based on amount paid."""
        self.balance_due = self.grand_total - self.amount_paid
        if self.balance_due <= decimal.Decimal("0"):
            self.status = self.Status.PAID
            self.paid_date = timezone.now().date()
        elif self.amount_paid > decimal.Decimal("0"):
            self.status = self.Status.PARTIALLY_PAID
        self.save(update_fields=["status", "balance_due", "paid_date", "amount_paid"])


# ═══════════════════════════════════════════════════════════════
# Payment
# ═══════════════════════════════════════════════════════════════

class Payment(models.Model):
    """
    A payment applied to one or more invoices.

    Supports: cash, card, transfer, insurance, and refunds.
    Refunds are tracked as negative-amount payments linked to the original.
    """

    class Method(models.TextChoices):
        CASH = "cash", "Cash"
        CARD = "card", "Card"
        TRANSFER = "transfer", "Bank Transfer"
        INSURANCE = "insurance", "Insurance"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="payments")
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name="payments")

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    method = models.CharField(max_length=20, choices=Method.choices)
    reference = models.CharField(max_length=100, blank=True, help_text="Transaction ID, check number, etc.")

    payment_date = models.DateTimeField(default=timezone.now)

    # Allocate payment to invoices
    allocations = models.JSONField(
        default=list,
        help_text='[{"invoice_id": "...", "amount": "50.00"}]',
    )

    # Refund support
    is_refund = models.BooleanField(default=False)
    original_payment = models.ForeignKey(
        "self", on_delete=models.PROTECT, null=True, blank=True,
        related_name="refunds",
    )
    refund_reason = models.TextField(blank=True)

    recorded_by = models.ForeignKey(
        "identity.User", on_delete=models.PROTECT, null=True, related_name="recorded_payments",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "billing_payment"
        ordering = ["-payment_date"]
        indexes = [
            models.Index(fields=["tenant"]),
            models.Index(fields=["tenant", "patient"]),
            models.Index(fields=["tenant", "method"]),
            models.Index(fields=["tenant", "payment_date"]),
        ]

    def __str__(self):
        sign = "-" if self.is_refund else ""
        return f"{sign}${abs(self.amount)} {self.method} — {self.patient.full_name}"

    def save(self, *args, **kwargs):
        """Apply payment allocations to invoices on save."""
        is_new = self._state.adding
        super().save(*args, **kwargs)

        if is_new and not self.is_refund and self.allocations:
            for alloc in self.allocations:
                try:
                    invoice = Invoice.objects.for_tenant(self.tenant).get(
                        id=alloc["invoice_id"],
                    )
                    amount = decimal.Decimal(str(alloc["amount"]))
                    invoice.amount_paid += amount
                    invoice.save(update_fields=["amount_paid"])
                    invoice.update_payment_status()
                except Invoice.DoesNotExist:
                    pass

        if is_new and self.is_refund:
            for alloc in self.allocations:
                try:
                    invoice = Invoice.objects.for_tenant(self.tenant).get(
                        id=alloc["invoice_id"],
                    )
                    amount = decimal.Decimal(str(alloc["amount"]))
                    invoice.amount_paid -= amount
                    invoice.update_payment_status()
                except Invoice.DoesNotExist:
                    pass


# ═══════════════════════════════════════════════════════════════
# Insurance Claim
# ═══════════════════════════════════════════════════════════════

class InsuranceClaim(models.Model):
    """Basic insurance claim tracking against invoices."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        PENDING = "pending", "Pending"
        APPROVED = "approved", "Approved"
        PARTIALLY_APPROVED = "partially_approved", "Partially Approved"
        DENIED = "denied", "Denied"
        PAID = "paid", "Paid"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="insurance_claims")
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name="insurance_claims")
    invoice = models.ForeignKey(Invoice, on_delete=models.PROTECT, related_name="insurance_claims")
    insurance_policy = models.ForeignKey(
        "patients.InsurancePolicy", on_delete=models.PROTECT, related_name="claims",
    )

    claim_number = models.CharField(max_length=50, unique=True)
    status = models.CharField(max_length=25, choices=Status.choices, default=Status.DRAFT)

    claimed_amount = models.DecimalField(max_digits=12, decimal_places=2)
    approved_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    denial_reason = models.TextField(blank=True)

    submitted_at = models.DateTimeField(null=True, blank=True)
    responded_at = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "billing_insurance_claim"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant"]),
            models.Index(fields=["tenant", "patient"]),
            models.Index(fields=["tenant", "status"]),
        ]

    def __str__(self):
        return f"Claim {self.claim_number} — {self.patient.full_name}"
