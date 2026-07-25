"""
Billing views — items, quotes, invoices, payments, POS, revenue dashboard.
"""
import decimal
import json
from django.utils import timezone
from django.db.models import Sum, Count, Q
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound, ValidationError
from drf_spectacular.utils import extend_schema

from tenancy.permissions import HasTenantAccess, TenantPermissionRequired
from patients.models import Patient
from .models import BillingItem, Quote, Invoice, Payment, InsuranceClaim
from . import serializers


def _generate_tenant(api_client):
    """Helper to get tenant from request context. Stub for POS/booking flows."""
    pass


# ═══════════════════════════════════════════════════════════════
# Billing Items
# ═══════════════════════════════════════════════════════════════

@extend_schema(tags=["billing"])
class BillingItemListView(generics.ListCreateAPIView):
    serializer_class = serializers.BillingItemSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "billing.read"

    def get_queryset(self):
        qs = BillingItem.objects.for_tenant(self.request.tenant).filter(is_active=True)
        category = self.request.query_params.get("category")
        if category:
            qs = qs.filter(category=category)
        return qs

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.tenant)


@extend_schema(tags=["billing"])
class BillingItemDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.BillingItemSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "billing.manage_items"

    def get_queryset(self):
        return BillingItem.objects.for_tenant(self.request.tenant)

    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active"])


# ═══════════════════════════════════════════════════════════════
# Quotes
# ═══════════════════════════════════════════════════════════════

@extend_schema(tags=["billing"])
class QuoteListView(generics.ListCreateAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return serializers.QuoteCreateSerializer
        return serializers.QuoteListSerializer

    def get_queryset(self):
        return Quote.objects.for_tenant(self.request.tenant).select_related("patient")

    def get_required_permission(self):
        return "billing.create_invoice" if self.request.method == "POST" else "billing.read"


@extend_schema(tags=["billing"])
class QuoteDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = serializers.QuoteDetailSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "billing.read"

    def get_queryset(self):
        return Quote.objects.for_tenant(self.request.tenant)


@extend_schema(tags=["billing"], summary="Convert quote to invoice")
class QuoteConvertView(generics.GenericAPIView):
    """Convert an accepted quote into an invoice."""
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "billing.create_invoice"

    def post(self, request, pk):
        try:
            quote = Quote.objects.for_tenant(request.tenant).get(pk=pk)
        except Quote.DoesNotExist:
            raise NotFound("Quote not found.")

        if quote.status not in (Quote.Status.ACCEPTED, Quote.Status.SENT, Quote.Status.DRAFT):
            raise ValidationError("Quote must be accepted before converting.")

        # Generate invoice number
        year = timezone.now().year
        count = Invoice.objects.for_tenant(request.tenant).filter(
            invoice_number__startswith=f"INV-{year}-",
        ).count() + 1
        invoice_number = f"INV-{year}-{count:05d}"

        invoice = Invoice.objects.create(
            tenant=request.tenant,
            patient=quote.patient,
            invoice_number=invoice_number,
            line_items=quote.line_items,
            subtotal=quote.subtotal,
            tax_total=quote.tax_total,
            discount_total=quote.discount_total,
            grand_total=quote.grand_total,
            notes=quote.notes,
            issued_date=timezone.now().date(),
            created_by=request.user,
        )

        quote.status = Quote.Status.CONVERTED
        quote.converted_invoice = invoice
        quote.save(update_fields=["status", "converted_invoice"])

        return Response(
            serializers.InvoiceDetailSerializer(invoice).data,
            status=status.HTTP_201_CREATED,
        )


# ═══════════════════════════════════════════════════════════════
# Invoices
# ═══════════════════════════════════════════════════════════════

@extend_schema(tags=["billing"])
class InvoiceListView(generics.ListCreateAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return serializers.InvoiceCreateSerializer
        return serializers.InvoiceListSerializer

    def get_queryset(self):
        qs = Invoice.objects.for_tenant(self.request.tenant).select_related("patient")
        status_filter = self.request.query_params.get("status")
        if status_filter:
            qs = qs.filter(status=status_filter)
        patient_id = self.request.query_params.get("patient")
        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        return qs

    def get_required_permission(self):
        return "billing.create_invoice" if self.request.method == "POST" else "billing.read"


@extend_schema(tags=["billing"])
class InvoiceDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return serializers.InvoiceCreateSerializer  # Re-use for editing line items
        return serializers.InvoiceDetailSerializer

    def get_queryset(self):
        return Invoice.objects.for_tenant(self.request.tenant).select_related("patient", "created_by")

    def get_required_permission(self):
        return "billing.create_invoice" if self.request.method in ("PUT", "PATCH", "DELETE") else "billing.read"

    def perform_destroy(self, instance):
        if instance.status == Invoice.Status.PAID:
            raise ValidationError("Cannot delete a paid invoice. Void it instead.")
        instance.status = Invoice.Status.CANCELLED
        instance.save(update_fields=["status"])


@extend_schema(tags=["billing"], summary="Issue a draft invoice")
class InvoiceIssueView(generics.GenericAPIView):
    """Issue a draft invoice — sets status to 'issued' with a due date."""
    serializer_class = serializers.InvoiceIssueSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "billing.create_invoice"

    def post(self, request, pk):
        try:
            invoice = Invoice.objects.for_tenant(request.tenant).get(pk=pk)
        except Invoice.DoesNotExist:
            raise NotFound("Invoice not found.")

        if invoice.status != Invoice.Status.DRAFT:
            raise ValidationError("Only draft invoices can be issued.")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        invoice.status = Invoice.Status.ISSUED
        invoice.issued_date = timezone.now().date()
        invoice.due_date = serializer.validated_data.get("due_date") or (
            timezone.now().date() + timezone.timedelta(days=30)
        )
        invoice.save(update_fields=["status", "issued_date", "due_date"])

        return Response(serializers.InvoiceDetailSerializer(invoice).data)


# ═══════════════════════════════════════════════════════════════
# Payments
# ═══════════════════════════════════════════════════════════════

@extend_schema(tags=["billing"])
class PaymentListView(generics.ListCreateAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return serializers.PaymentCreateSerializer
        return serializers.PaymentSerializer

    def get_queryset(self):
        return Payment.objects.for_tenant(self.request.tenant).select_related("patient", "recorded_by")

    def get_required_permission(self):
        return "billing.process_payment" if self.request.method == "POST" else "billing.read"


@extend_schema(tags=["billing"], summary="Process refund")
class RefundView(generics.GenericAPIView):
    """Create a refund against a previous payment."""
    serializer_class = serializers.RefundCreateSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "billing.refund"

    def post(self, request, payment_pk):
        try:
            original = Payment.objects.for_tenant(request.tenant).get(pk=payment_pk)
        except Payment.DoesNotExist:
            raise NotFound("Payment not found.")

        if original.is_refund:
            raise ValidationError("Cannot refund a refund.")

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refund_amount = serializer.validated_data["amount"]
        if refund_amount > original.amount:
            raise ValidationError("Refund amount exceeds original payment.")

        refund = Payment.objects.create(
            tenant=request.tenant,
            patient=original.patient,
            amount=-refund_amount,
            method=original.method,
            reference=f"REFUND-{original.reference or original.id}",
            is_refund=True,
            original_payment=original,
            refund_reason=serializer.validated_data["reason"],
            allocations=original.allocations,
            recorded_by=request.user,
        )

        return Response(
            serializers.PaymentSerializer(refund).data,
            status=status.HTTP_201_CREATED,
        )


# ═══════════════════════════════════════════════════════════════
# POS Quick Checkout
# ═══════════════════════════════════════════════════════════════

@extend_schema(tags=["billing"], summary="POS quick checkout")
class POSCheckoutView(generics.GenericAPIView):
    """
    Quick sale: select items → apply discount → record payment → done.

    Creates an invoice + payment in one atomic step for walk-in payments.
    """
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "billing.process_payment"

    def post(self, request):
        data = request.data
        patient_id = data.get("patient_id")
        line_items = data.get("line_items", [])
        discount = decimal.Decimal(str(data.get("discount", "0")))
        payment_method = data.get("payment_method", "cash")
        payment_reference = data.get("payment_reference", "")

        if not line_items:
            return Response({"error": "At least one item required."}, status=status.HTTP_400_BAD_REQUEST)

        tenant = request.tenant

        # Verify patient if provided
        if patient_id:
            try:
                Patient.objects.for_tenant(tenant).get(pk=patient_id)
            except Patient.DoesNotExist:
                return Response({"error": "Patient not found."}, status=status.HTTP_404_NOT_FOUND)

        # Calculate totals
        serialized_items = []
        for item in line_items:
            serialized_items.append({
                "billing_item_id": str(item.get("billing_item_id", "")),
                "description": item.get("description", ""),
                "quantity": item.get("quantity", 1),
                "unit_price": str(item.get("unit_price", "0")),
                "tax_rate": str(item.get("tax_rate", "0")),
            })

        totals = Quote.calculate_totals(serialized_items, discount)
        grand_total = totals["grand_total"]

        # Create invoice
        year = timezone.now().year
        count = Invoice.objects.for_tenant(tenant).filter(
            invoice_number__startswith=f"INV-{year}-",
        ).count() + 1
        invoice_number = f"INV-{year}-{count:05d}"

        invoice = Invoice.objects.create(
            tenant=tenant,
            patient_id=patient_id,
            invoice_number=invoice_number,
            line_items=serialized_items,
            **totals,
            status=Invoice.Status.PAID,
            issued_date=timezone.now().date(),
            paid_date=timezone.now().date(),
            amount_paid=grand_total,
            balance_due=decimal.Decimal("0"),
            created_by=request.user,
        )

        # Record payment
        Payment.objects.create(
            tenant=tenant,
            patient_id=patient_id,
            amount=grand_total,
            method=payment_method,
            reference=payment_reference or f"POS-{invoice_number}",
            allocations=[{"invoice_id": str(invoice.id), "amount": str(grand_total)}],
            recorded_by=request.user,
        )

        return Response({
            "invoice": serializers.InvoiceDetailSerializer(invoice).data,
            "message": "Payment processed successfully.",
        }, status=status.HTTP_201_CREATED)


# ═══════════════════════════════════════════════════════════════
# Revenue Dashboard
# ═══════════════════════════════════════════════════════════════

@extend_schema(tags=["billing"], summary="Revenue summary")
class RevenueDashboardView(generics.GenericAPIView):
    """
    Aggregated revenue data for operational dashboards.

    GET /api/billing/revenue/?period=month&date=2024-01-01
    """
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "billing.view_finance"

    def get(self, request):
        period = request.query_params.get("period", "month")
        tenant = request.tenant

        # Determine date range
        today = timezone.now().date()
        if period == "today":
            start = today
            end = today + timezone.timedelta(days=1)
        elif period == "week":
            start = today - timezone.timedelta(days=today.weekday())
            end = start + timezone.timedelta(days=7)
        elif period == "year":
            start = today.replace(month=1, day=1)
            end = today.replace(year=today.year + 1, month=1, day=1)
        else:  # month
            start = today.replace(day=1)
            if today.month == 12:
                end = today.replace(year=today.year + 1, month=1, day=1)
            else:
                end = today.replace(month=today.month + 1, day=1)

        invoices = Invoice.objects.for_tenant(tenant).filter(
            issued_date__gte=start, issued_date__lt=end,
        ).exclude(status__in=[Invoice.Status.CANCELLED, Invoice.Status.VOID])

        payments = Payment.objects.for_tenant(tenant).filter(
            payment_date__gte=timezone.make_aware(
                timezone.datetime.combine(start, timezone.datetime.min.time()),
            ),
            payment_date__lt=timezone.make_aware(
                timezone.datetime.combine(end, timezone.datetime.min.time()),
            ),
            is_refund=False,
        )

        revenue = payments.aggregate(total=Sum("amount"))["total"] or decimal.Decimal("0")
        invoiced = invoices.aggregate(total=Sum("grand_total"))["total"] or decimal.Decimal("0")
        collected = payments.aggregate(total=Sum("amount"))["total"] or decimal.Decimal("0")

        return Response({
            "period": period,
            "date_range": {"start": str(start), "end": str(end)},
            "total_revenue": str(invoiced),
            "total_collected": str(collected),
            "total_outstanding": str(invoiced - collected),
            "invoice_count": invoices.count(),
            "payment_count": payments.count(),
        })


# ═══════════════════════════════════════════════════════════════
# Insurance Claims
# ═══════════════════════════════════════════════════════════════

@extend_schema(tags=["billing"])
class InsuranceClaimListView(generics.ListCreateAPIView):
    serializer_class = serializers.InsuranceClaimSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "billing.read"

    def get_queryset(self):
        return InsuranceClaim.objects.for_tenant(self.request.tenant).select_related("patient")

    def perform_create(self, serializer):
        tenant = self.request.tenant
        count = InsuranceClaim.objects.for_tenant(tenant).count() + 1
        serializer.save(tenant=tenant, claim_number=f"CLM-{count:06d}")


@extend_schema(tags=["billing"])
class InsuranceClaimDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = serializers.InsuranceClaimSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "billing.read"

    def get_queryset(self):
        return InsuranceClaim.objects.for_tenant(self.request.tenant)


@extend_schema(tags=["billing"])
class CheckoutSessionView(generics.GenericAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    serializer_class = serializers.CheckoutSessionSerializer

    def get_required_permission(self):
        return "billing.create_payment"

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            invoice = Invoice.objects.for_tenant(request.tenant).get(
                id=serializer.validated_data["invoice_id"],
            )
        except Invoice.DoesNotExist:
            raise NotFound("Invoice not found.")
        if invoice.balance_due <= 0:
            return Response({"error": "Invoice is already paid"}, status=400)
        from .gateway import PaymentGatewayService
        service = PaymentGatewayService(request.tenant)
        result = service.create_checkout_session(
            invoice,
            serializer.validated_data["success_url"],
            serializer.validated_data["cancel_url"],
            serializer.validated_data.get("gateway", "stripe"),
        )
        if "error" in result:
            return Response(result, status=400)
        return Response(result)


@method_decorator(csrf_exempt, name="dispatch")
class StripeWebhookView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        from .gateway import PaymentGatewayService
        payload = request.body
        sig_header = request.META.get("HTTP_STRIPE_SIGNATURE", "")
        result = PaymentGatewayService(None).handle_webhook(payload, sig_header, "stripe")
        return JsonResponse(result)
