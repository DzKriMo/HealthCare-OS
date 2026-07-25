"""
Dental module API views — tooth chart, procedures, treatment plans.
"""
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from drf_spectacular.utils import extend_schema

from tenancy.permissions import HasTenantAccess, TenantPermissionRequired
from patients.models import Patient
from .models import (
    ToothChart, Tooth, ToothProcedure, Implant, Crown,
    DentalTreatmentPlan, TreatmentPlanPhase, PlannedProcedure,
)
from . import serializers


def _get_chart(tenant, patient_id):
    """Get or create a tooth chart for a patient."""
    chart, _ = ToothChart.objects.get_or_create(
        tenant=tenant, patient_id=patient_id,
    )
    # Initialize teeth if needed
    if not chart.teeth.exists():
        _initialize_teeth(chart, tenant)
    return chart


def _initialize_teeth(chart, tenant):
    """Create all 32 permanent teeth (FDI 11-48) for a new chart."""
    teeth = []
    for quadrant_start in [1, 2, 3, 4]:
        for tooth_num in range(1, 9):
            fdi = quadrant_start * 10 + tooth_num
            teeth.append(Tooth(chart=chart, tenant=tenant, fdi_number=fdi))
    Tooth.objects.bulk_create(teeth)


# ═══════════════════════════════════════════════════════════════
# Tooth Chart
# ═══════════════════════════════════════════════════════════════

@extend_schema(tags=["dental"])
class ChartView(generics.RetrieveAPIView):
    """Get a patient's full tooth chart (odontogram)."""
    serializer_class = serializers.ToothChartSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "dental.chart.read"

    def get_object(self):
        patient_id = self.kwargs["patient_pk"]
        try:
            Patient.objects.for_tenant(self.request.tenant).get(pk=patient_id)
        except Patient.DoesNotExist:
            raise NotFound("Patient not found.")
        return _get_chart(self.request.tenant, patient_id)


@extend_schema(tags=["dental"])
class ToothDetailView(generics.RetrieveUpdateAPIView):
    """Get or update a single tooth's condition."""
    permission_classes = [HasTenantAccess, TenantPermissionRequired]

    def get_serializer_class(self):
        if self.request.method in ("PUT", "PATCH"):
            return serializers.ToothUpdateSerializer
        return serializers.ToothSerializer

    def get_queryset(self):
        return Tooth.objects.filter(chart__tenant=self.request.tenant)

    def get_required_permission(self):
        return "dental.chart.write" if self.request.method in ("PUT", "PATCH") else "dental.chart.read"


# ═══════════════════════════════════════════════════════════════
# Procedures
# ═══════════════════════════════════════════════════════════════

@extend_schema(tags=["dental"])
class ProcedureListView(generics.ListCreateAPIView):
    """List or record dental procedures. Filter by patient or tooth."""
    permission_classes = [HasTenantAccess, TenantPermissionRequired]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return serializers.ToothProcedureCreateSerializer
        return serializers.ToothProcedureSerializer

    def get_queryset(self):
        qs = ToothProcedure.objects.for_tenant(self.request.tenant).select_related("tooth", "performed_by")
        patient_id = self.request.query_params.get("patient")
        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        tooth_id = self.request.query_params.get("tooth")
        if tooth_id:
            qs = qs.filter(tooth_id=tooth_id)
        return qs

    def get_required_permission(self):
        return "dental.procedures.perform" if self.request.method == "POST" else "dental.procedures.read"


@extend_schema(tags=["dental"])
class ProcedureDetailView(generics.RetrieveAPIView):
    serializer_class = serializers.ToothProcedureSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "dental.procedures.read"

    def get_queryset(self):
        return ToothProcedure.objects.for_tenant(self.request.tenant)


# ═══════════════════════════════════════════════════════════════
# Implants & Crowns
# ═══════════════════════════════════════════════════════════════

@extend_schema(tags=["dental"])
class ImplantListView(generics.ListCreateAPIView):
    serializer_class = serializers.ImplantSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "dental.chart.read"

    def get_queryset(self):
        return Implant.objects.for_tenant(self.request.tenant).select_related("tooth")

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.tenant)


@extend_schema(tags=["dental"])
class CrownListView(generics.ListCreateAPIView):
    serializer_class = serializers.CrownSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "dental.chart.read"

    def get_queryset(self):
        return Crown.objects.for_tenant(self.request.tenant).select_related("tooth")

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.tenant)


# ═══════════════════════════════════════════════════════════════
# Treatment Plans
# ═══════════════════════════════════════════════════════════════

@extend_schema(tags=["dental"])
class TreatmentPlanListView(generics.ListCreateAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]

    def get_serializer_class(self):
        if self.request.method == "POST":
            return serializers.TreatmentPlanCreateSerializer
        return serializers.TreatmentPlanSerializer

    def get_queryset(self):
        qs = DentalTreatmentPlan.objects.for_tenant(self.request.tenant).prefetch_related(
            "phases__procedures",
        ).select_related("patient", "created_by")
        patient_id = self.request.query_params.get("patient")
        if patient_id:
            qs = qs.filter(patient_id=patient_id)
        return qs

    def get_required_permission(self):
        return "dental.treatment_plan.write" if self.request.method == "POST" else "dental.treatment_plan.read"


@extend_schema(tags=["dental"])
class TreatmentPlanDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = serializers.TreatmentPlanSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "dental.treatment_plan.read"

    def get_queryset(self):
        return DentalTreatmentPlan.objects.for_tenant(self.request.tenant).prefetch_related(
            "phases__procedures",
        )


@extend_schema(tags=["dental"], summary="Get dental dashboard data")
class DentalDashboardView(generics.GenericAPIView):
    """Aggregated data for dental dashboard widgets."""
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "dental.chart.read"

    def get(self, request):
        tenant = request.tenant
        from django.utils import timezone
        today = timezone.now().date()

        today_procedures = ToothProcedure.objects.for_tenant(tenant).filter(
            performed_at__date=today,
        ).count()

        pending_plans = DentalTreatmentPlan.objects.for_tenant(tenant).filter(
            status__in=["presented", "accepted", "in_progress"],
        ).count()

        return Response({
            "today_procedures": today_procedures,
            "pending_plans": pending_plans,
        })
