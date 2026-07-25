"""Gynecology views."""
from rest_framework import generics
from drf_spectacular.utils import extend_schema
from tenancy.permissions import HasTenantAccess, TenantPermissionRequired
from .models import OBHistory, PapSmear, AntenatalVisit
from . import serializers


@extend_schema(tags=["gyn"])
class OBHistoryView(generics.RetrieveUpdateAPIView):
    serializer_class = serializers.OBHistorySerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "gyn.read"
    def get_object(self):
        obj, _ = OBHistory.objects.get_or_create(tenant=self.request.tenant, patient_id=self.kwargs["patient_pk"])
        return obj

@extend_schema(tags=["gyn"])
class PapSmearListView(generics.ListCreateAPIView):
    serializer_class = serializers.PapSmearSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "gyn.read"
    def get_queryset(self):
        qs = PapSmear.objects.for_tenant(self.request.tenant)
        pid = self.request.query_params.get("patient")
        if pid: qs = qs.filter(patient_id=pid)
        return qs
    def get_required_permission(self):
        return "gyn.write" if self.request.method == "POST" else "gyn.read"
    def perform_create(self, s): s.save(tenant=self.request.tenant, performed_by=self.request.user)

@extend_schema(tags=["gyn"])
class AntenatalListView(generics.ListCreateAPIView):
    serializer_class = serializers.AntenatalSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "gyn.read"
    def get_queryset(self):
        qs = AntenatalVisit.objects.for_tenant(self.request.tenant)
        pid = self.request.query_params.get("patient")
        if pid: qs = qs.filter(patient_id=pid)
        return qs
    def get_required_permission(self):
        return "gyn.write" if self.request.method == "POST" else "gyn.read"
    def perform_create(self, s): s.save(tenant=self.request.tenant, practitioner=self.request.user)
