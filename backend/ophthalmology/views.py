"""Ophthalmology views."""
from rest_framework import generics
from drf_spectacular.utils import extend_schema
from tenancy.permissions import HasTenantAccess, TenantPermissionRequired
from .models import EyeExam, LensPrescription
from . import serializers


@extend_schema(tags=["ophth"])
class ExamListView(generics.ListCreateAPIView):
    serializer_class = serializers.EyeExamSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    def get_queryset(self):
        qs = EyeExam.objects.for_tenant(self.request.tenant).select_related("patient","practitioner")
        pid = self.request.query_params.get("patient")
        if pid: qs = qs.filter(patient_id=pid)
        return qs
    def get_required_permission(self):
        return "ophth.write" if self.request.method == "POST" else "ophth.read"
    def perform_create(self, s): s.save(tenant=self.request.tenant, practitioner=self.request.user)


@extend_schema(tags=["ophth"])
class ExamDetailView(generics.RetrieveAPIView):
    serializer_class = serializers.EyeExamSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "ophth.read"
    def get_queryset(self): return EyeExam.objects.for_tenant(self.request.tenant)


@extend_schema(tags=["ophth"])
class PrescriptionListView(generics.ListCreateAPIView):
    serializer_class = serializers.LensPrescriptionSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "ophth.read"
    def get_queryset(self):
        qs = LensPrescription.objects.for_tenant(self.request.tenant)
        pid = self.request.query_params.get("patient")
        if pid: qs = qs.filter(patient_id=pid)
        return qs
    def perform_create(self, s): s.save(tenant=self.request.tenant, prescribed_by=self.request.user)
