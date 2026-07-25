"""Pharmacy views — prescriptions, dispensing, controlled substances."""
from django.utils import timezone
from django.db import models as db_models
from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from drf_spectacular.utils import extend_schema

from tenancy.permissions import HasTenantAccess, TenantPermissionRequired
from .models import Prescription, DispenseRecord, ControlledSubstanceLog
from inventory.models import InventoryItem
from . import serializers


@extend_schema(tags=["pharmacy"])
class PrescriptionListView(generics.ListCreateAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return serializers.PrescriptionCreateSerializer
        return serializers.PrescriptionListSerializer

    def get_queryset(self):
        qs = Prescription.objects.for_tenant(self.request.tenant).select_related("patient", "prescribed_by")
        patient_id = self.request.query_params.get("patient")
        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        status_f = self.request.query_params.get("status")
        if status_f:
            qs = qs.filter(status=status_f)
        if self.request.query_params.get("controlled") == "true":
            qs = qs.filter(is_controlled=True)
        return qs

    def get_required_permission(self):
        return "pharmacy.prescribe" if self.request.method == "POST" else "pharmacy.read"


@extend_schema(tags=["pharmacy"])
class PrescriptionDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = serializers.PrescriptionDetailSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "pharmacy.read"

    def get_queryset(self):
        return Prescription.objects.for_tenant(self.request.tenant).prefetch_related("dispense_records")


@extend_schema(tags=["pharmacy"])
class DispenseListView(generics.ListCreateAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return serializers.DispenseCreateSerializer
        return serializers.DispenseRecordSerializer

    def get_queryset(self):
        return DispenseRecord.objects.for_tenant(self.request.tenant).select_related(
            "prescription", "patient", "dispensed_by",
        )

    def get_required_permission(self):
        return "pharmacy.dispense" if self.request.method == "POST" else "pharmacy.read"


@extend_schema(tags=["pharmacy"])
class PharmacyPOSView(views.APIView):
    """
    Pharmacy retail POS: dispense + charge in one call.

    POST /api/pharmacy/pos/
    Body: prescription_id, quantity, batch_id, inventory_item_id, copay, payment_method
    """
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "pharmacy.dispense"

    def post(self, request):
        rx_id = request.data.get("prescription_id")
        qty = request.data.get("quantity")
        batch_id = request.data.get("batch_id")
        item_id = request.data.get("inventory_item_id")
        copay = request.data.get("copay", "0")
        payment_method = request.data.get("payment_method", "cash")
        notes = request.data.get("notes", "")

        if not rx_id or not qty:
            return Response({"error": "prescription_id and quantity required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            rx = Prescription.objects.for_tenant(request.tenant).get(pk=rx_id)
        except Prescription.DoesNotExist:
            return Response({"error": "Prescription not found."}, status=status.HTTP_404_NOT_FOUND)

        if rx.status == Prescription.Status.CANCELLED:
            return Response({"error": "Prescription is cancelled."}, status=status.HTTP_400_BAD_REQUEST)

        # Create dispense record
        import decimal as _d
        qty = _d.Decimal(str(request.data["quantity"]))
        dispense = DispenseRecord.objects.create(
            tenant=request.tenant, prescription=rx, patient=rx.patient,
            quantity=qty, batch_id=batch_id,
            inventory_item_id=item_id, copay_charged=copay,
            is_refill=rx.quantity_dispensed > 0, refill_number=rx.refills_used + 1 if rx.quantity_dispensed > 0 else 0,
            dispensed_by=request.user, notes=notes,
        )

        # Controlled substance logging
        if rx.is_controlled:
            item = InventoryItem.objects.for_tenant(request.tenant).get(id=item_id) if item_id else None
            ControlledSubstanceLog.objects.create(
                tenant=request.tenant, dispense_record=dispense, prescription=rx,
                witness_id=request.data.get("witness_id"),
                quantity_before_dispense=item.quantity_on_hand if item else _d.Decimal("0"),
                quantity_after_dispense=(item.quantity_on_hand - qty) if item else _d.Decimal("0"),
                count_verified=request.data.get("count_verified", False),
            )

        return Response({
            "dispense": serializers.DispenseRecordSerializer(dispense).data,
            "prescription_status": rx.status,
            "refills_remaining": rx.refills_remaining,
        }, status=status.HTTP_201_CREATED)


@extend_schema(tags=["pharmacy"])
class ControlledLogListView(generics.ListAPIView):
    serializer_class = serializers.ControlledLogSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "pharmacy.controlled"

    def get_queryset(self):
        return ControlledSubstanceLog.objects.for_tenant(self.request.tenant).select_related(
            "prescription", "dispense_record__dispensed_by", "witness",
        )


@extend_schema(tags=["pharmacy"], summary="Pharmacy dashboard")
class PharmacyDashboardView(views.APIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "pharmacy.read"

    def get(self, request):
        tenant = request.tenant
        today = timezone.now().date()

        pending = Prescription.objects.for_tenant(tenant).filter(
            status__in=["issued", "partially_filled"],
        ).count()

        dispensed_today = DispenseRecord.objects.for_tenant(tenant).filter(
            dispensed_at__date=today,
        ).count()

        controlled_today = ControlledSubstanceLog.objects.for_tenant(tenant).filter(
            logged_at__date=today,
        ).count()

        return Response({
            "pending_prescriptions": pending,
            "dispensed_today": dispensed_today,
            "controlled_logs_today": controlled_today,
        })
