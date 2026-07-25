"""Orthopedics views."""
from rest_framework import generics
from drf_spectacular.utils import extend_schema
from tenancy.permissions import HasTenantAccess, TenantPermissionRequired
from .models import JointAssessment, FractureRecord, PhysiotherapyPlan
from . import serializers


@extend_schema(tags=["ortho"])
class JointListView(generics.ListCreateAPIView):
    serializer_class = serializers.JointSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "ortho.read"
    def get_queryset(self):
        qs = JointAssessment.objects.for_tenant(self.request.tenant)
        pid = self.request.query_params.get("patient")
        if pid: qs = qs.filter(patient_id=pid)
        return qs
    def get_required_permission(self):
        return "ortho.write" if self.request.method == "POST" else "ortho.read"
    def perform_create(self, s): s.save(tenant=self.request.tenant, performed_by=self.request.user)

@extend_schema(tags=["ortho"])
class FractureListView(generics.ListCreateAPIView):
    serializer_class = serializers.FractureSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "ortho.read"
    def get_queryset(self):
        qs = FractureRecord.objects.for_tenant(self.request.tenant)
        pid = self.request.query_params.get("patient")
        if pid: qs = qs.filter(patient_id=pid)
        return qs
    def get_required_permission(self):
        return "ortho.write" if self.request.method == "POST" else "ortho.read"
    def perform_create(self, s): s.save(tenant=self.request.tenant, diagnosed_by=self.request.user)

@extend_schema(tags=["ortho"])
class PhysioListView(generics.ListCreateAPIView):
    serializer_class = serializers.PhysioPlanSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "ortho.read"
    def get_queryset(self):
        qs = PhysiotherapyPlan.objects.for_tenant(self.request.tenant)
        pid = self.request.query_params.get("patient")
        if pid: qs = qs.filter(patient_id=pid)
        return qs
    def get_required_permission(self):
        return "ortho.write" if self.request.method == "POST" else "ortho.read"
    def perform_create(self, s): s.save(tenant=self.request.tenant, created_by=self.request.user)
