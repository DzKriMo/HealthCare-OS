from rest_framework import generics; from drf_spectacular.utils import extend_schema
from tenancy.permissions import HasTenantAccess, TenantPermissionRequired
from .models import EmergencyVisit; from . import serializers

@extend_schema(tags=["er"])
class ERVisitListView(generics.ListCreateAPIView):
    serializer_class = serializers.ERVisitSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]; required_permission = "er.read"
    def get_queryset(self):
        qs = EmergencyVisit.objects.for_tenant(self.request.tenant)
        pid = self.request.query_params.get("patient")
        if pid: qs = qs.filter(patient_id=pid)
        return qs
    def get_required_permission(self): return "er.write" if self.request.method == "POST" else "er.read"
    def perform_create(self, s): s.save(tenant=self.request.tenant, practitioner=self.request.user)
