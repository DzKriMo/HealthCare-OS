from rest_framework import generics; from drf_spectacular.utils import extend_schema
from tenancy.permissions import HasTenantAccess, TenantPermissionRequired
from .models import DialysisSession; from . import serializers

@extend_schema(tags=["dialysis"])
class DialysisSessionListView(generics.ListCreateAPIView):
    serializer_class = serializers.DialysisSessionSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]; required_permission = "dialysis.read"
    def get_queryset(self):
        qs = DialysisSession.objects.for_tenant(self.request.tenant)
        pid = self.request.query_params.get("patient")
        if pid: qs = qs.filter(patient_id=pid)
        return qs
    def get_required_permission(self):
        return "dialysis.write" if self.request.method == "POST" else "dialysis.read"
    def perform_create(self, s): s.save(tenant=self.request.tenant, practitioner=self.request.user)
