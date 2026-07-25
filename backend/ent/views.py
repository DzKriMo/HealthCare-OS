"""ENT views."""
from rest_framework import generics
from drf_spectacular.utils import extend_schema
from tenancy.permissions import HasTenantAccess, TenantPermissionRequired
from .models import AudiologyExam, EndoscopyRecord
from . import serializers


@extend_schema(tags=["ent"])
class AudiologyListView(generics.ListCreateAPIView):
    serializer_class = serializers.AudiologySerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "ent.read"
    def get_queryset(self):
        qs = AudiologyExam.objects.for_tenant(self.request.tenant)
        pid = self.request.query_params.get("patient")
        if pid: qs = qs.filter(patient_id=pid)
        return qs
    def get_required_permission(self):
        return "ent.write" if self.request.method == "POST" else "ent.read"
    def perform_create(self, s): s.save(tenant=self.request.tenant, performed_by=self.request.user)

@extend_schema(tags=["ent"])
class EndoscopyListView(generics.ListCreateAPIView):
    serializer_class = serializers.EndoscopySerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "ent.read"
    def get_queryset(self):
        qs = EndoscopyRecord.objects.for_tenant(self.request.tenant)
        pid = self.request.query_params.get("patient")
        if pid: qs = qs.filter(patient_id=pid)
        return qs
    def get_required_permission(self):
        return "ent.write" if self.request.method == "POST" else "ent.read"
    def perform_create(self, s): s.save(tenant=self.request.tenant, performed_by=self.request.user)
