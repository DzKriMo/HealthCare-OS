"""
Inventory models — Sprint B1.

Core entities:
    InventoryItem — medicines, supplies, equipment with categories, units, cost/price.
    StockMovement — every in/out/adjust/transfer tracked immutably.
    Supplier — vendor info, lead times, pricing.
    PurchaseOrder — create → send → receive workflow.
    Batch — lot numbers, manufacturing date, expiration tracking.
"""
import uuid
import decimal
from django.db import models
from django.core.exceptions import ValidationError
import datetime as _datetime
from django.utils import timezone
from tenancy.models import Tenant
from tenancy.managers import TenantScopedManager


class Supplier(models.Model):
    """Vendor/supplier for inventory items."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="suppliers")
    name = models.CharField(max_length=200)
    contact_person = models.CharField(max_length=200, blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.TextField(blank=True)
    lead_time_days = models.IntegerField(default=7, help_text="Typical delivery time in days.")
    payment_terms = models.CharField(max_length=100, blank=True, help_text="e.g. Net 30")
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "inventory_supplier"
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "name"], name="unique_supplier_per_tenant"),
        ]

    def __str__(self):
        return self.name


class InventoryItem(models.Model):
    """
    A stockable item — medicine, supply, equipment, or packaged product.

    Category determines behavior: medicines track batches + expirations,
    supplies are simpler, equipment may not decrement on use.
    """

    class Category(models.TextChoices):
        MEDICINE = "medicine", "Medicine"
        SUPPLY = "supply", "Medical Supply"
        EQUIPMENT = "equipment", "Equipment"
        CONSUMABLE = "consumable", "Consumable"
        OTHER = "other", "Other"

    class Unit(models.TextChoices):
        TABLET = "tablet", "Tablet"
        CAPSULE = "capsule", "Capsule"
        BOTTLE = "bottle", "Bottle"
        VIAL = "vial", "Vial"
        BOX = "box", "Box"
        PIECE = "piece", "Piece"
        PACK = "pack", "Pack"
        ML = "ml", "Milliliter"
        L = "l", "Liter"
        G = "g", "Gram"
        KG = "kg", "Kilogram"
        OTHER = "other", "Other"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="inventory_items")
    supplier = models.ForeignKey(Supplier, on_delete=models.SET_NULL, null=True, blank=True, related_name="items")

    name = models.CharField(max_length=300)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.SUPPLY)
    unit = models.CharField(max_length=10, choices=Unit.choices, default=Unit.PIECE)
    sku = models.CharField(max_length=100, blank=True, help_text="Internal stock-keeping unit code.")
    barcode = models.CharField(max_length=100, blank=True, help_text="UPC/EAN barcode number.")

    # Stock
    quantity_on_hand = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    reorder_point = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Trigger reorder when stock falls below this.")
    reorder_quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Pricing
    unit_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    unit_price = models.DecimalField(max_digits=12, decimal_places=2, default=0, help_text="Selling price to patient.")

    # Tracking
    requires_batch_tracking = models.BooleanField(default=False, help_text="Track lot numbers and expirations.")
    requires_refrigeration = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "inventory_item"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["tenant"]),
            models.Index(fields=["tenant", "category"]),
            models.Index(fields=["tenant", "sku"]),
            models.Index(fields=["tenant", "barcode"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["tenant", "sku"], name="unique_sku_per_tenant", condition=~models.Q(sku="")),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_category_display()}) — {self.quantity_on_hand} {self.get_unit_display()}"

    @property
    def is_low_stock(self) -> bool:
        return self.quantity_on_hand <= self.reorder_point and self.reorder_point > 0

    @property
    def stock_value(self) -> decimal.Decimal:
        return self.quantity_on_hand * self.unit_cost


class Batch(models.Model):
    """Lot/batch tracking for medicines and expirable items."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name="batches")
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)

    lot_number = models.CharField(max_length=100)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    manufacturing_date = models.DateField(null=True, blank=True)
    expiration_date = models.DateField(null=True, blank=True)
    received_date = models.DateField(default=_datetime.date.today)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "inventory_batch"
        ordering = ["expiration_date"]
        verbose_name_plural = "batches"
        indexes = [
            models.Index(fields=["item"]),
            models.Index(fields=["tenant"]),
            models.Index(fields=["expiration_date"]),
        ]
        constraints = [
            models.UniqueConstraint(fields=["item", "lot_number"], name="unique_lot_per_item"),
        ]

    def __str__(self):
        return f"Lot {self.lot_number} — {self.item.name} (qty: {self.quantity})"

    @property
    def is_expired(self) -> bool:
        return self.expiration_date is not None and self.expiration_date < timezone.now().date()

    @property
    def days_until_expiry(self) -> int | None:
        if not self.expiration_date:
            return None
        return (self.expiration_date - timezone.now().date()).days

    @property
    def is_expiring_soon(self) -> bool:
        days = self.days_until_expiry
        return days is not None and 0 <= days <= 90


class StockMovement(models.Model):
    """
    Immutable record of every stock change. Never edited, never deleted.

    Types: in (received), out (dispensed/sold), adjustment (inventory count correction),
           transfer (between locations), waste (expired/damaged).
    """

    class MovementType(models.TextChoices):
        IN = "in", "Stock In (Received)"
        OUT = "out", "Stock Out (Dispensed/Used)"
        ADJUSTMENT = "adjustment", "Adjustment (Count Correction)"
        TRANSFER = "transfer", "Transfer"
        WASTE = "waste", "Waste (Expired/Damaged)"
        RETURN = "return", "Return"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="stock_movements")
    item = models.ForeignKey(InventoryItem, on_delete=models.CASCADE, related_name="stock_movements")
    batch = models.ForeignKey(Batch, on_delete=models.SET_NULL, null=True, blank=True, related_name="movements")

    movement_type = models.CharField(max_length=15, choices=MovementType.choices)
    quantity = models.DecimalField(max_digits=12, decimal_places=2, help_text="Positive for in, negative for out.")
    quantity_before = models.DecimalField(max_digits=12, decimal_places=2)
    quantity_after = models.DecimalField(max_digits=12, decimal_places=2)

    reference_type = models.CharField(max_length=100, blank=True, help_text="PO, Invoice, Encounter, etc.")
    reference_id = models.CharField(max_length=100, blank=True)
    reason = models.TextField(blank=True)

    performed_by = models.ForeignKey("identity.User", on_delete=models.PROTECT, null=True, related_name="stock_movements")
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "inventory_stock_movement"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant"]),
            models.Index(fields=["item"]),
            models.Index(fields=["movement_type"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        arrow = "+" if self.quantity > 0 else ""
        return f"{self.get_movement_type_display()}: {arrow}{self.quantity} {self.item.name}"

    def save(self, *args, **kwargs):
        if self._state.adding:
            self.quantity_before = self.item.quantity_on_hand
            self.quantity_after = self.quantity_before + self.quantity
            self.item.quantity_on_hand = self.quantity_after
            self.item.save(update_fields=["quantity_on_hand", "updated_at"])

            # Also update batch quantity if batch-tracked
            if self.batch:
                self.batch.quantity += self.quantity
                self.batch.save(update_fields=["quantity"])
        super().save(*args, **kwargs)


class PurchaseOrder(models.Model):
    """Purchase order to a supplier — create, send, receive workflow."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SENT = "sent", "Sent to Supplier"
        PARTIALLY_RECEIVED = "partially_received", "Partially Received"
        RECEIVED = "received", "Fully Received"
        CANCELLED = "cancelled", "Cancelled"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="purchase_orders")
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="purchase_orders")
    po_number = models.CharField(max_length=30, db_index=True)

    status = models.CharField(max_length=25, choices=Status.choices, default=Status.DRAFT)
    notes = models.TextField(blank=True)

    # Line items: [{"item_id": "...", "name": "...", "quantity": 10, "unit_cost": "5.00"}]
    line_items = models.JSONField(default=list)
    total_cost = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    ordered_by = models.ForeignKey("identity.User", on_delete=models.PROTECT, null=True, related_name="purchase_orders")
    ordered_date = models.DateField(null=True, blank=True)
    expected_date = models.DateField(null=True, blank=True)
    received_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "inventory_purchase_order"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["tenant"]),
            models.Index(fields=["supplier"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"PO {self.po_number} — {self.supplier.name} ({self.status})"

    def receive(self, user, item_receipts: list[dict]):
        """Receive items against this PO. item_receipts: [{"item_id": ..., "quantity": ...}]"""
        for receipt in item_receipts:
            try:
                item = InventoryItem.objects.for_tenant(self.tenant).get(id=receipt["item_id"])
                qty = decimal.Decimal(str(receipt["quantity"]))
                StockMovement.objects.create(
                    tenant=self.tenant,
                    item=item,
                    movement_type=StockMovement.MovementType.IN,
                    quantity=qty,
                    reference_type="purchase_order",
                    reference_id=str(self.id),
                    reason=f"Received PO {self.po_number}",
                    performed_by=user,
                )
            except InventoryItem.DoesNotExist:
                pass

        # Check if all line items are fully received
        all_received = True
        for li in self.line_items:
            li_id = li.get("item_id", "")
            li_qty = decimal.Decimal(str(li.get("quantity", 0)))
            received_qty = decimal.Decimal("0")
            for r in item_receipts:
                if r.get("item_id") == li_id:
                    received_qty += decimal.Decimal(str(r.get("quantity", 0)))
            if received_qty < li_qty:
                all_received = False
                break

        self.status = self.Status.RECEIVED if all_received else self.Status.PARTIALLY_RECEIVED
        self.received_date = timezone.now().date() if all_received else None
        self.save(update_fields=["status", "received_date"])
