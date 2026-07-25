"""
Serializers for billing domain.
"""
import decimal
from django.utils import timezone
from rest_framework import serializers
from .models import BillingItem, Quote, Invoice, Payment, InsuranceClaim


# ── Billing Item ────────────────────────────────────────────

class BillingItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = BillingItem
        fields = [
            "id", "name", "description", "category",
            "price", "tax_rate", "accounting_code",
            "is_active", "is_package",
        ]
        read_only_fields = ["id"]


# ── Quote ──────────────────────────────────────────────────

class QuoteLineItemSerializer(serializers.Serializer):
    billing_item_id = serializers.UUIDField(required=False, allow_null=True)
    description = serializers.CharField(max_length=500)
    quantity = serializers.IntegerField(min_value=1, default=1)
    unit_price = serializers.DecimalField(max_digits=12, decimal_places=2)
    tax_rate = serializers.DecimalField(max_digits=5, decimal_places=2, default=0)


class QuoteListSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)

    class Meta:
        model = Quote
        fields = [
            "id", "patient", "patient_name", "quote_number",
            "status", "grand_total", "valid_until", "created_at",
        ]


class QuoteDetailSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)

    class Meta:
        model = Quote
        fields = [
            "id", "tenant", "patient", "patient_name",
            "quote_number", "status",
            "line_items", "subtotal", "tax_total", "discount_total", "grand_total",
            "notes", "valid_until",
            "created_by", "created_by_name", "created_at", "updated_at",
            "converted_invoice",
        ]
        read_only_fields = ["id", "tenant", "quote_number", "status", "converted_invoice", "created_at", "updated_at"]


class QuoteCreateSerializer(serializers.ModelSerializer):
    line_items = QuoteLineItemSerializer(many=True)
    discount_total = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)

    class Meta:
        model = Quote
        fields = [
            "patient", "line_items", "discount_total",
            "notes", "valid_until",
        ]

    def create(self, validated_data):
        tenant = self.context["request"].tenant
        user = self.context["request"].user
        line_items = validated_data.pop("line_items")
        discount = validated_data.pop("discount_total", decimal.Decimal("0"))

        # Calculate totals
        serialized_items = [
            {
                "billing_item_id": str(item.get("billing_item_id", "")),
                "description": item["description"],
                "quantity": item.get("quantity", 1),
                "unit_price": str(item["unit_price"]),
                "tax_rate": str(item.get("tax_rate", "0")),
            }
            for item in line_items
        ]
        totals = Quote.calculate_totals(serialized_items, discount)

        # Generate quote number
        count = Quote.objects.for_tenant(tenant).count() + 1
        quote_number = f"QTE-{count:06d}"

        return Quote.objects.create(
            tenant=tenant,
            quote_number=quote_number,
            created_by=user,
            line_items=serialized_items,
            **totals,
            discount_total=discount,
            **validated_data,
        )


# ── Invoice ────────────────────────────────────────────────

class InvoiceListSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)

    class Meta:
        model = Invoice
        fields = [
            "id", "patient", "patient_name", "invoice_number",
            "status", "grand_total", "amount_paid", "balance_due",
            "issued_date", "due_date", "created_at",
        ]


class InvoiceDetailSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    created_by_name = serializers.CharField(source="created_by.full_name", read_only=True)
    is_paid = serializers.BooleanField(read_only=True)

    class Meta:
        model = Invoice
        fields = [
            "id", "tenant", "patient", "patient_name",
            "invoice_number", "status",
            "line_items", "subtotal", "tax_total", "discount_total",
            "grand_total", "amount_paid", "balance_due", "is_paid",
            "issued_date", "due_date", "paid_date",
            "notes", "internal_notes",
            "created_by", "created_by_name", "created_at", "updated_at",
        ]
        read_only_fields = [
            "id", "tenant", "invoice_number", "status", "amount_paid",
            "balance_due", "paid_date", "created_at", "updated_at",
        ]


class InvoiceCreateSerializer(serializers.ModelSerializer):
    line_items = QuoteLineItemSerializer(many=True)
    discount_total = serializers.DecimalField(max_digits=12, decimal_places=2, default=0)
    id = serializers.UUIDField(read_only=True)
    invoice_number = serializers.CharField(read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    tax_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    grand_total = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    status = serializers.CharField(read_only=True)

    class Meta:
        model = Invoice
        fields = [
            "id", "invoice_number",
            "patient", "line_items", "discount_total",
            "subtotal", "tax_total", "grand_total", "status",
            "notes", "internal_notes", "due_date",
        ]
        read_only_fields = ["id", "invoice_number", "subtotal", "tax_total", "grand_total", "status"]

    def create(self, validated_data):
        tenant = self.context["request"].tenant
        user = self.context["request"].user
        line_items = validated_data.pop("line_items")
        discount = validated_data.pop("discount_total", decimal.Decimal("0"))

        serialized_items = [
            {
                "billing_item_id": str(item.get("billing_item_id", "")),
                "description": item["description"],
                "quantity": item.get("quantity", 1),
                "unit_price": str(item["unit_price"]),
                "tax_rate": str(item.get("tax_rate", "0")),
            }
            for item in line_items
        ]
        totals = Quote.calculate_totals(serialized_items, discount)

        # Generate invoice number per tenant
        today = timezone.now()
        year = today.year
        count = Invoice.objects.for_tenant(tenant).filter(
            invoice_number__startswith=f"INV-{year}-",
        ).count() + 1
        invoice_number = f"INV-{year}-{count:05d}"

        return Invoice.objects.create(
            tenant=tenant,
            invoice_number=invoice_number,
            created_by=user,
            line_items=serialized_items,
            issued_date=today.date(),
            **totals,
            **validated_data,
        )


class InvoiceIssueSerializer(serializers.Serializer):
    """Issue a draft invoice (makes it official)."""
    due_date = serializers.DateField(required=False)


# ── Payment ────────────────────────────────────────────────

class PaymentSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    recorded_by_name = serializers.CharField(source="recorded_by.full_name", read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id", "patient", "patient_name", "amount", "method",
            "reference", "payment_date", "allocations",
            "is_refund", "original_payment", "refund_reason",
            "recorded_by", "recorded_by_name", "created_at",
        ]
        read_only_fields = ["id", "recorded_by", "created_at"]


class PaymentCreateSerializer(serializers.ModelSerializer):
    allocations = serializers.JSONField(default=list)

    class Meta:
        model = Payment
        fields = [
            "patient", "amount", "method", "reference",
            "payment_date", "allocations",
        ]

    def create(self, validated_data):
        tenant = self.context["request"].tenant
        user = self.context["request"].user
        return Payment.objects.create(
            tenant=tenant,
            recorded_by=user,
            **validated_data,
        )


class RefundCreateSerializer(serializers.Serializer):
    """Create a refund against a previous payment."""
    amount = serializers.DecimalField(max_digits=12, decimal_places=2, min_value=decimal.Decimal("0.01"))
    reason = serializers.CharField(max_length=500)


# ── Insurance Claim ────────────────────────────────────────

class InsuranceClaimSerializer(serializers.ModelSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)

    class Meta:
        model = InsuranceClaim
        fields = [
            "id", "patient", "patient_name", "invoice", "insurance_policy",
            "claim_number", "status", "claimed_amount", "approved_amount",
            "denial_reason", "submitted_at", "responded_at", "notes",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "claim_number", "status", "approved_amount", "submitted_at", "responded_at", "created_at", "updated_at"]


# ── Revenue Dashboard ──────────────────────────────────────

class RevenueSummarySerializer(serializers.Serializer):
    """Aggregated revenue data for dashboards."""
    period = serializers.CharField()
    total_revenue = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_collected = serializers.DecimalField(max_digits=14, decimal_places=2)
    total_outstanding = serializers.DecimalField(max_digits=14, decimal_places=2)
    invoice_count = serializers.IntegerField()
    payment_count = serializers.IntegerField()
    by_practitioner = serializers.JSONField()
    by_category = serializers.JSONField()
