from rest_framework import generics; from drf_spectacular.utils import extend_schema
from tenancy.permissions import HasTenantAccess, TenantPermissionRequired
from .models import CancerStaging, ChemotherapyProtocol, TumorMarker; from . import serializers

def _qsv(view, qs, pid_param="patient"):
    r = view.request; pid = r.query_params.get(pid_param); return qs.filter(patient_id=pid) if pid else qs

@extend_schema(tags=["onc"])
class StagingListView(generics.ListCreateAPIView):
    serializer_class = serializers.StagingSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]; required_permission = "onc.read"
    def get_queryset(self): return _qsv(self, CancerStaging.objects.for_tenant(self.request.tenant))
    def get_required_permission(self): return "onc.write" if self.request.method == "POST" else "onc.read"
    def perform_create(self, s): s.save(tenant=self.request.tenant, recorded_by=self.request.user)

@extend_schema(tags=["onc"])
class ChemoListView(generics.ListCreateAPIView):
    serializer_class = serializers.ChemoSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]; required_permission = "onc.read"
    def get_queryset(self): return _qsv(self, ChemotherapyProtocol.objects.for_tenant(self.request.tenant))
    def get_required_permission(self): return "onc.write" if self.request.method == "POST" else "onc.read"
    def perform_create(self, s): s.save(tenant=self.request.tenant, prescribed_by=self.request.user)

@extend_schema(tags=["onc"])
class TumorMarkerView(generics.ListCreateAPIView):
    serializer_class = serializers.TumorMarkerSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]; required_permission = "onc.read"
    def get_queryset(self): return _qsv(self, TumorMarker.objects.for_tenant(self.request.tenant))
    def get_required_permission(self): return "onc.write" if self.request.method == "POST" else "onc.read"
    def perform_create(self, s): s.save(tenant=self.request.tenant)
