"""Cardiology views."""
from rest_framework import generics
from drf_spectacular.utils import extend_schema
from tenancy.permissions import HasTenantAccess, TenantPermissionRequired
from .models import ECGRecord, EchoReport, BPReading, CVRiskScore
from . import serializers


@extend_schema(tags=["cardio"])
class ECGListView(generics.ListCreateAPIView):
    serializer_class = serializers.ECGSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "cardio.read" if "GET" else "cardio.write"
    def get_queryset(self):
        qs = ECGRecord.objects.for_tenant(self.request.tenant).select_related("patient")
        pid = self.request.query_params.get("patient")
        if pid: qs = qs.filter(patient_id=pid)
        return qs
    def get_required_permission(self):
        return "cardio.write" if self.request.method == "POST" else "cardio.read"
    def perform_create(self, s): s.save(tenant=self.request.tenant, performed_by=self.request.user)

@extend_schema(tags=["cardio"])
class EchoListView(generics.ListCreateAPIView):
    serializer_class = serializers.EchoSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "cardio.read"
    def get_queryset(self):
        qs = EchoReport.objects.for_tenant(self.request.tenant).select_related("patient")
        pid = self.request.query_params.get("patient")
        if pid: qs = qs.filter(patient_id=pid)
        return qs
    def get_required_permission(self):
        return "cardio.write" if self.request.method == "POST" else "cardio.read"
    def perform_create(self, s): s.save(tenant=self.request.tenant, performed_by=self.request.user)

@extend_schema(tags=["cardio"])
class BPListView(generics.ListCreateAPIView):
    serializer_class = serializers.BPReadingSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "cardio.read"
    def get_queryset(self):
        qs = BPReading.objects.for_tenant(self.request.tenant)
        pid = self.request.query_params.get("patient")
        if pid: qs = qs.filter(patient_id=pid)
        return qs
    def perform_create(self, s): s.save(tenant=self.request.tenant)

@extend_schema(tags=["cardio"])
class CVDashboardView(generics.GenericAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "cardio.read"
    def get(self, request):
        tenant = request.tenant
        abnormal_ecgs = ECGRecord.objects.for_tenant(tenant).filter(is_abnormal=True).count()
        high_risk = CVRiskScore.objects.for_tenant(tenant).filter(risk_category="high").count()
        return Response({"abnormal_ecgs":abnormal_ecgs,"high_risk_patients":high_risk})

from rest_framework.response import Response
