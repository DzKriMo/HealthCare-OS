from rest_framework import generics; from drf_spectacular.utils import extend_schema
from tenancy.permissions import HasTenantAccess, TenantPermissionRequired
from .models import PhysiotherapySession; from . import serializers

@extend_schema(tags=["physio"])
class PhysioSessionListView(generics.ListCreateAPIView):
    serializer_class = serializers.PhysioSessionSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]; required_permission = "physio.read"
    def get_queryset(self):
        qs = PhysiotherapySession.objects.for_tenant(self.request.tenant)
        pid = self.request.query_params.get("patient")
        if pid: qs = qs.filter(patient_id=pid)
        return qs
    def get_required_permission(self):
        return "physio.write" if self.request.method == "POST" else "physio.read"
    def perform_create(self, s): s.save(tenant=self.request.tenant, practitioner=self.request.user)
