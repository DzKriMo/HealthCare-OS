"""Pediatrics views."""
from rest_framework import generics
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from django.utils import timezone
from tenancy.permissions import HasTenantAccess, TenantPermissionRequired
from .models import GrowthRecord, VaccinationSchedule, DevelopmentalMilestone
from . import serializers


@extend_schema(tags=["peds"])
class GrowthListView(generics.ListCreateAPIView):
    serializer_class = serializers.GrowthRecordSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "peds.read"
    def get_queryset(self):
        qs = GrowthRecord.objects.for_tenant(self.request.tenant)
        pid = self.request.query_params.get("patient")
        if pid: qs = qs.filter(patient_id=pid)
        return qs
    def get_required_permission(self):
        return "peds.write" if self.request.method == "POST" else "peds.read"
    def perform_create(self, s): s.save(tenant=self.request.tenant, recorded_by=self.request.user)

@extend_schema(tags=["peds"])
class VaxScheduleListView(generics.ListCreateAPIView):
    serializer_class = serializers.VaxScheduleSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "peds.read"
    def get_queryset(self):
        qs = VaccinationSchedule.objects.for_tenant(self.request.tenant)
        pid = self.request.query_params.get("patient")
        if pid: qs = qs.filter(patient_id=pid)
        return qs
    def perform_create(self, s): s.save(tenant=self.request.tenant)

@extend_schema(tags=["peds"])
class MilestoneListView(generics.ListCreateAPIView):
    serializer_class = serializers.MilestoneSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "peds.read"
    def get_queryset(self):
        qs = DevelopmentalMilestone.objects.for_tenant(self.request.tenant)
        pid = self.request.query_params.get("patient")
        if pid: qs = qs.filter(patient_id=pid)
        return qs
    def get_required_permission(self):
        return "peds.write" if self.request.method == "POST" else "peds.read"
    def perform_create(self, s): s.save(tenant=self.request.tenant, recorded_by=self.request.user)

@extend_schema(tags=["peds"])
class PedsDashboardView(generics.GenericAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "peds.read"
    def get(self, request):
        tenant = request.tenant
        overdue_vax = VaccinationSchedule.objects.for_tenant(tenant).filter(status="overdue").count()
        delayed_milestones = DevelopmentalMilestone.objects.for_tenant(tenant).filter(is_delayed=True).count()
        return Response({"overdue_vaccinations":overdue_vax,"delayed_milestones":delayed_milestones})
