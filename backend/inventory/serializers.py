"""Serializers for inventory module."""
import decimal
from rest_framework import serializers
from .models import InventoryItem, StockMovement, Supplier, PurchaseOrder, Batch


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = ["id", "name", "contact_person", "email", "phone", "address", "lead_time_days", "payment_terms", "is_active", "notes"]
        read_only_fields = ["id"]


class InventoryItemSerializer(serializers.ModelSerializer):
    is_low_stock = serializers.BooleanField(read_only=True)
    stock_value = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)

    class Meta:
        model = InventoryItem
        fields = [
            "id", "name", "category", "unit", "sku", "barcode",
            "quantity_on_hand", "reorder_point", "reorder_quantity",
            "unit_cost", "unit_price",
            "requires_batch_tracking", "requires_refrigeration",
            "is_low_stock", "stock_value",
            "supplier", "supplier_name", "is_active", "notes",
        ]
        read_only_fields = ["id", "quantity_on_hand", "stock_value"]


class InventoryItemCreateSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)

    class Meta:
        model = InventoryItem
        fields = [
            "id", "name", "category", "unit", "sku", "barcode",
            "reorder_point", "reorder_quantity", "unit_cost", "unit_price",
            "requires_batch_tracking", "requires_refrigeration",
            "supplier", "notes",
        ]

    def create(self, validated_data):
        tenant = self.context["request"].tenant
        return InventoryItem.objects.create(tenant=tenant, **validated_data)


class BatchSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source="item.name", read_only=True)
    is_expired = serializers.BooleanField(read_only=True)
    days_until_expiry = serializers.IntegerField(read_only=True, allow_null=True)
    is_expiring_soon = serializers.BooleanField(read_only=True)

    class Meta:
        model = Batch
        fields = [
            "id", "item", "item_name", "lot_number", "quantity",
            "manufacturing_date", "expiration_date", "received_date",
            "is_expired", "days_until_expiry", "is_expiring_soon",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        tenant = self.context["request"].tenant
        return Batch.objects.create(tenant=tenant, **validated_data)


class StockMovementSerializer(serializers.ModelSerializer):
    item_name = serializers.CharField(source="item.name", read_only=True)
    performed_by_name = serializers.CharField(source="performed_by.full_name", read_only=True)

    class Meta:
        model = StockMovement
        fields = [
            "id", "item", "item_name", "batch", "movement_type",
            "quantity", "quantity_before", "quantity_after",
            "reference_type", "reference_id", "reason",
            "performed_by", "performed_by_name", "created_at",
        ]
        read_only_fields = ["id", "quantity_before", "quantity_after", "performed_by", "created_at"]


class StockAdjustmentSerializer(serializers.Serializer):
    item_id = serializers.UUIDField()
    quantity = serializers.DecimalField(max_digits=12, decimal_places=2)
    movement_type = serializers.ChoiceField(choices=["adjustment", "waste", "return"])
    reason = serializers.CharField(max_length=500, required=False, allow_blank=True)
    batch_id = serializers.UUIDField(required=False, allow_null=True)


class PurchaseOrderSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source="supplier.name", read_only=True)
    ordered_by_name = serializers.CharField(source="ordered_by.full_name", read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = [
            "id", "supplier", "supplier_name", "po_number",
            "status", "notes", "line_items", "total_cost",
            "ordered_by", "ordered_by_name",
            "ordered_date", "expected_date", "received_date",
            "created_at",
        ]
        read_only_fields = ["id", "po_number", "status", "ordered_by", "received_date", "created_at"]


class PurchaseOrderCreateSerializer(serializers.ModelSerializer):
    id = serializers.UUIDField(read_only=True)
    po_number = serializers.CharField(read_only=True)

    class Meta:
        model = PurchaseOrder
        fields = [
            "id", "supplier", "po_number", "notes", "line_items",
            "expected_date",
        ]

    def create(self, validated_data):
        tenant = self.context["request"].tenant
        user = self.context["request"].user
        count = PurchaseOrder.objects.for_tenant(tenant).count() + 1
        po_number = f"PO-{timezone.now().year}-{count:05d}"

        total = decimal.Decimal("0")
        for li in validated_data.get("line_items", []):
            qty = decimal.Decimal(str(li.get("quantity", 0)))
            cost = decimal.Decimal(str(li.get("unit_cost", 0)))
            total += qty * cost

        return PurchaseOrder.objects.create(
            tenant=tenant, po_number=po_number, ordered_by=user,
            total_cost=total, **validated_data,
        )


from django.utils import timezone


class POReceiveSerializer(serializers.Serializer):
    item_receipts = serializers.JSONField(default=list)
