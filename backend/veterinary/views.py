from rest_framework import generics; from drf_spectacular.utils import extend_schema
from tenancy.permissions import HasTenantAccess, TenantPermissionRequired
from .models import AnimalRecord, RabiesCertificate; from . import serializers

@extend_schema(tags=["vet"])
class AnimalRecordView(generics.RetrieveUpdateAPIView):
    serializer_class = serializers.AnimalRecordSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]; required_permission = "vet.read"
    def get_object(self):
        obj, _ = AnimalRecord.objects.get_or_create(tenant=self.request.tenant, patient_id=self.kwargs["patient_pk"])
        return obj

@extend_schema(tags=["vet"])
class RabiesCertListView(generics.ListCreateAPIView):
    serializer_class = serializers.RabiesCertSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]; required_permission = "vet.read"
    def get_queryset(self): return RabiesCertificate.objects.for_tenant(self.request.tenant)
    def get_required_permission(self): return "vet.write" if self.request.method == "POST" else "vet.read"
    def perform_create(self, s): s.save(tenant=self.request.tenant)
