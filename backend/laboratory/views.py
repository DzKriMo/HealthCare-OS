"""Lab views — catalog, orders, specimens, results, dashboard."""
from django.utils import timezone
from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from drf_spectacular.utils import extend_schema
from tenancy.permissions import HasTenantAccess, TenantPermissionRequired
from .models import TestCatalog, LabOrder, Specimen, LabResult
from . import serializers


@extend_schema(tags=["lab"])
class TestCatalogView(generics.ListCreateAPIView):
    serializer_class = serializers.TestCatalogSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "lab.read"

    def get_queryset(self):
        return TestCatalog.objects.for_tenant(self.request.tenant).filter(is_active=True)
    def perform_create(self, s): s.save(tenant=self.request.tenant)


@extend_schema(tags=["lab"])
class LabOrderListView(generics.ListCreateAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    def get_serializer_class(self):
        return serializers.LabOrderCreateSerializer if self.request.method == "POST" else serializers.LabOrderSerializer
    def get_queryset(self):
        qs = LabOrder.objects.for_tenant(self.request.tenant).select_related("patient")
        pid = self.request.query_params.get("patient")
        if pid: qs = qs.filter(patient_id=pid)
        return qs
    def get_required_permission(self):
        return "lab.order" if self.request.method == "POST" else "lab.read"


@extend_schema(tags=["lab"])
class LabOrderDetailView(generics.RetrieveAPIView):
    serializer_class = serializers.LabOrderSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "lab.read"
    def get_queryset(self): return LabOrder.objects.for_tenant(self.request.tenant).prefetch_related("results","specimens")


@extend_schema(tags=["lab"])
class SpecimenListView(generics.ListCreateAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    def get_serializer_class(self):
        return serializers.SpecimenCreateSerializer if self.request.method == "POST" else serializers.SpecimenSerializer
    def get_queryset(self): return Specimen.objects.for_tenant(self.request.tenant).select_related("collected_by")
    def get_required_permission(self):
        return "lab.collect" if self.request.method == "POST" else "lab.read"


@extend_schema(tags=["lab"])
class SpecimenTransitionView(views.APIView):
    """Transition specimen: receive / process / complete / reject."""
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "lab.collect"
    def post(self, request, pk):
        try: s = Specimen.objects.for_tenant(request.tenant).get(pk=pk)
        except Specimen.DoesNotExist: return Response({"error":"Not found"}, status=404)
        target = request.data.get("status"); reason = request.data.get("reason","")
        if target not in ["received","processing","completed","rejected"]:
            return Response({"error":"Invalid status"}, status=400)
        if target == "rejected": s.rejection_reason = reason
        s.transition_to(target)
        return Response(serializers.SpecimenSerializer(s).data)


@extend_schema(tags=["lab"])
class LabResultListView(generics.ListCreateAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    def get_serializer_class(self):
        return serializers.LabResultCreateSerializer if self.request.method == "POST" else serializers.LabResultSerializer
    def get_queryset(self):
        qs = LabResult.objects.for_tenant(self.request.tenant).select_related("test")
        oid = self.request.query_params.get("order")
        if oid: qs = qs.filter(lab_order_id=oid)
        return qs
    def get_required_permission(self):
        return "lab.result" if self.request.method == "POST" else "lab.read"


@extend_schema(tags=["lab"])
class LabResultApproveView(views.APIView):
    """Review or approve a result."""
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    def post(self, request, pk):
        try: r = LabResult.objects.for_tenant(request.tenant).get(pk=pk)
        except LabResult.DoesNotExist: return Response({"error":"Not found"}, status=404)
        s = serializers.LabResultApproveSerializer(data=request.data)
        s.is_valid(raise_exception=True)
        action = s.validated_data["action"]
        if action == "review":
            r.status = LabResult.Status.REVIEWED; r.reviewed_by = request.user; r.reviewed_at = timezone.now()
        elif action == "approve":
            if r.status != LabResult.Status.REVIEWED:
                return Response({"error":"Must be reviewed first"}, status=400)
            r.status = LabResult.Status.APPROVED; r.approved_by = request.user; r.approved_at = timezone.now()
        elif action == "amend":
            r.status = LabResult.Status.AMENDED
        r.save()
        return Response(serializers.LabResultSerializer(r).data)


@extend_schema(tags=["lab"])
class LabDashboardView(views.APIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "lab.read"
    def get(self, request):
        tenant = request.tenant
        pending = LabResult.objects.for_tenant(tenant).filter(status="draft").count()
        critical = LabResult.objects.for_tenant(tenant).filter(is_critical=True, status__in=["draft","reviewed"]).count()
        orders_today = LabOrder.objects.for_tenant(tenant).filter(ordered_at__date=timezone.now().date()).count()
        return Response({"pending_results":pending,"critical_results":critical,"orders_today":orders_today})
