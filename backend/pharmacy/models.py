"""
Pharmacy models — Sprint B2.

Core entities:
    Prescription — drug orders from encounters with workflow.
    DispenseRecord — each fulfillment of a prescription.
    ControlledSubstanceLog — mandatory tracking log.
"""
import uuid
import decimal
from django.db import models
from django.utils import timezone
from tenancy.models import Tenant
from tenancy.managers import TenantScopedManager
from patients.models import Patient
from inventory.models import InventoryItem


class Prescription(models.Model):
    """
    A medication prescription issued during an encounter.

    Status flow: draft → issued → partially_filled → filled → cancelled
    """

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        ISSUED = "issued", "Issued"
        PARTIALLY_FILLED = "partially_filled", "Partially Filled"
        FILLED = "filled", "Filled"
        CANCELLED = "cancelled", "Cancelled"
        EXPIRED = "expired", "Expired"

    class Route(models.TextChoices):
        ORAL = "oral", "Oral"
        SUBLINGUAL = "sublingual", "Sublingual"
        TOPICAL = "topical", "Topical"
        INHALED = "inhaled", "Inhaled"
        IV = "iv", "Intravenous"
        IM = "im", "Intramuscular"
        SC = "sc", "Subcutaneous"
        RECTAL = "rectal", "Rectal"
        OPHTHALMIC = "ophthalmic", "Ophthalmic"
        OTIC = "otic", "Otic"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="prescriptions")
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name="prescriptions")
    encounter = models.ForeignKey(
        "scheduling.Appointment", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="prescriptions", help_text="Encounter where this was prescribed.",
    )

    # Drug
    drug_name = models.CharField(max_length=300)
    drug_code = models.CharField(max_length=50, blank=True, help_text="NDC or DIN code.")
    inventory_item = models.ForeignKey(
        InventoryItem, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="prescriptions",
    )
    dosage = models.CharField(max_length=100, help_text="e.g. 500mg")
    frequency = models.CharField(max_length=100, help_text="e.g. TID, QID, q6h")
    duration_days = models.IntegerField(null=True, blank=True)
    route = models.CharField(max_length=20, choices=Route.choices, default=Route.ORAL)
    instructions = models.TextField(blank=True, help_text="Sig: take with food, etc.")

    # Quantity & Refills
    quantity_prescribed = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_dispensed = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    refills_authorized = models.IntegerField(default=0)
    refills_used = models.IntegerField(default=0)
    daw = models.BooleanField(default=False, help_text="Dispense as written — no substitution.")

    # Controlled substance
    is_controlled = models.BooleanField(default=False)
    controlled_schedule = models.CharField(
        max_length=10, blank=True,
        choices=[("II","II"),("III","III"),("IV","IV"),("V","V")],
    )

    # Status & Dates
    status = models.CharField(max_length=25, choices=Status.choices, default=Status.DRAFT)
    issued_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True, help_text="Prescription expires on this date.")

    # Auth
    prescribed_by = models.ForeignKey(
        "identity.User", on_delete=models.PROTECT, null=True, related_name="prescriptions",
    )
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "pharmacy_prescription"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant"]),
            models.Index(fields=["patient"]),
            models.Index(fields=["status"]),
            models.Index(fields=["is_controlled"]),
        ]

    def __str__(self):
        return f"{self.drug_name} {self.dosage} — {self.patient.full_name}"

    @property
    def refills_remaining(self) -> int:
        return max(0, self.refills_authorized - self.refills_used)

    @property
    def is_expired(self) -> bool:
        if self.expiry_date:
            return self.expiry_date < timezone.now().date()
        return False


class DispenseRecord(models.Model):
    """
    Each time a prescription is filled/refilled.

    Tracks: pharmacist, quantity dispensed, lot number, copay charged.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="dispense_records")
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name="dispense_records")
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name="dispense_records")

    quantity = models.DecimalField(max_digits=10, decimal_places=2)
    batch = models.ForeignKey(
        "inventory.Batch", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="dispense_records",
    )
    inventory_item = models.ForeignKey(
        InventoryItem, on_delete=models.SET_NULL, null=True, blank=True,
    )
    copay_charged = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    is_refill = models.BooleanField(default=False)
    refill_number = models.IntegerField(default=0)

    dispensed_by = models.ForeignKey(
        "identity.User", on_delete=models.PROTECT, null=True, related_name="dispensed",
    )
    dispensed_at = models.DateTimeField(auto_now_add=True)
    notes = models.TextField(blank=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "pharmacy_dispense"
        ordering = ["-dispensed_at"]
        indexes = [
            models.Index(fields=["tenant"]),
            models.Index(fields=["prescription"]),
        ]

    def __str__(self):
        return f"{self.quantity} {self.prescription.drug_name} → {self.patient.full_name}"

    def save(self, *args, **kwargs):
        """Auto-update prescription dispensed quantity and refill count."""
        is_new = self._state.adding
        super().save(*args, **kwargs)
        if is_new:
            rx = self.prescription
            rx.quantity_dispensed += self.quantity
            if self.is_refill:
                rx.refills_used += 1
            if rx.quantity_dispensed >= rx.quantity_prescribed and rx.refills_remaining == 0:
                rx.status = Prescription.Status.FILLED
            elif rx.quantity_dispensed > 0:
                rx.status = Prescription.Status.PARTIALLY_FILLED
            rx.save(update_fields=["quantity_dispensed", "refills_used", "status"])

            # Deduct from inventory
            if self.inventory_item:
                from inventory.models import StockMovement
                StockMovement.objects.create(
                    tenant=self.tenant,
                    item=self.inventory_item,
                    batch=self.batch,
                    movement_type=StockMovement.MovementType.OUT,
                    quantity=-self.quantity,
                    reference_type="dispense",
                    reference_id=str(self.id),
                    reason=f"Dispensed Rx {rx.id}",
                    performed_by=self.dispensed_by,
                )


class ControlledSubstanceLog(models.Model):
    """
    Mandatory log for Schedule II-V controlled substances.

    Every dispense of a controlled substance must be logged with
    a witness (for Schedule II) and inventory count verified.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="controlled_logs")
    dispense_record = models.OneToOneField(
        DispenseRecord, on_delete=models.CASCADE, related_name="controlled_log",
    )
    prescription = models.ForeignKey(Prescription, on_delete=models.CASCADE, related_name="controlled_logs")

    # Witness
    witness = models.ForeignKey(
        "identity.User", on_delete=models.PROTECT, null=True, blank=True,
        related_name="witnessed_dispenses",
        help_text="Required for Schedule II.",
    )
    witness_signature = models.TextField(blank=True, help_text="SVG signature data.")

    # Inventory verification
    quantity_before_dispense = models.DecimalField(max_digits=10, decimal_places=2)
    quantity_after_dispense = models.DecimalField(max_digits=10, decimal_places=2)
    count_verified = models.BooleanField(default=False)

    notes = models.TextField(blank=True)
    logged_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "pharmacy_controlled_log"
        ordering = ["-logged_at"]

    def __str__(self):
        return f"Controlled: {self.prescription.drug_name} — {self.dispense_record.quantity} units"
