"""Dermatology views."""
from rest_framework import generics, status, views
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from tenancy.permissions import HasTenantAccess, TenantPermissionRequired
from patients.models import Patient
from .models import BodyMap, Lesion, LesionPhoto, DermatologyProcedure
from . import serializers


@extend_schema(tags=["derm"])
class BodyMapView(generics.RetrieveAPIView):
    serializer_class = serializers.BodyMapSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "derm.read"

    def get_object(self):
        patient_id = self.kwargs["patient_pk"]
        map_obj, _ = BodyMap.objects.get_or_create(
            tenant=self.request.tenant, patient_id=patient_id,
        )
        return map_obj


@extend_schema(tags=["derm"])
class LesionListView(generics.ListCreateAPIView):
    serializer_class = serializers.LesionSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "derm.read" if "GET" else "derm.write"

    def get_queryset(self):
        return Lesion.objects.for_tenant(self.request.tenant).filter(patient_id=self.kwargs["patient_pk"])
    def perform_create(self, s):
        body_map, _ = BodyMap.objects.get_or_create(
            tenant=self.request.tenant, patient_id=self.kwargs["patient_pk"],
        )
        s.save(tenant=self.request.tenant, patient_id=self.kwargs["patient_pk"],
               body_map=body_map, recorded_by=self.request.user)
    def get_required_permission(self):
        return "derm.write" if self.request.method == "POST" else "derm.read"


@extend_schema(tags=["derm"])
class LesionDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = serializers.LesionSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "derm.read"
    def get_queryset(self): return Lesion.objects.for_tenant(self.request.tenant)


@extend_schema(tags=["derm"])
class ProcedureListView(generics.ListCreateAPIView):
    serializer_class = serializers.ProcedureSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "derm.read"
    def get_queryset(self): return DermatologyProcedure.objects.for_tenant(self.request.tenant)
    def perform_create(self, s): s.save(tenant=self.request.tenant, performed_by=self.request.user)
