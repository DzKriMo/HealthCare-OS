"""Clinical views — encounters, diagnoses, referrals, vitals, vaccinations, history."""
from django.utils import timezone
from rest_framework import generics, status, views
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from tenancy.permissions import HasTenantAccess, TenantPermissionRequired
from .models import Encounter, Diagnosis, Referral, VitalSigns, Vaccination, FamilyHistory, SocialHistory
from . import serializers


@extend_schema(tags=["clinical"])
class EncounterListView(generics.ListCreateAPIView):
    serializer_class = serializers.EncounterSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    def get_queryset(self):
        qs = Encounter.objects.for_tenant(self.request.tenant).select_related("patient","practitioner")
        pid = self.request.query_params.get("patient")
        if pid: qs = qs.filter(patient_id=pid)
        return qs
    def get_required_permission(self):
        return "clinical.write" if self.request.method == "POST" else "clinical.read"

@extend_schema(tags=["clinical"])
class EncounterDetailView(generics.RetrieveUpdateAPIView):
    serializer_class = serializers.EncounterSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "clinical.read"
    def get_queryset(self): return Encounter.objects.for_tenant(self.request.tenant)

@extend_schema(tags=["clinical"])
class EncounterSignView(views.APIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "clinical.write"
    def post(self, request, pk):
        try: e = Encounter.objects.for_tenant(request.tenant).get(pk=pk)
        except Encounter.DoesNotExist: return Response({"error":"Not found"}, status=404)
        e.status = Encounter.Status.SIGNED; e.signed_by = request.user; e.signed_at = timezone.now()
        e.save()
        return Response(serializers.EncounterSerializer(e).data)

@extend_schema(tags=["clinical"])
class DiagnosisListView(generics.ListCreateAPIView):
    serializer_class = serializers.DiagnosisSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "clinical.diagnose" if "POST" else "clinical.read"
    def get_queryset(self):
        qs = Diagnosis.objects.for_tenant(self.request.tenant)
        pid = self.request.query_params.get("patient")
        if pid: qs = qs.filter(patient_id=pid)
        return qs
    def get_required_permission(self):
        return "clinical.diagnose" if self.request.method == "POST" else "clinical.read"

@extend_schema(tags=["clinical"])
class ReferralListView(generics.ListCreateAPIView):
    serializer_class = serializers.ReferralSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "clinical.refer"
    def get_queryset(self): return Referral.objects.for_tenant(self.request.tenant)

@extend_schema(tags=["clinical"])
class VitalSignsListView(generics.ListCreateAPIView):
    serializer_class = serializers.VitalSignsSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "clinical.read"
    def get_queryset(self):
        qs = VitalSigns.objects.for_tenant(self.request.tenant)
        pid = self.request.query_params.get("patient")
        if pid: qs = qs.filter(patient_id=pid)
        return qs
    def perform_create(self, s): s.save(tenant=self.request.tenant, recorded_by=self.request.user)

@extend_schema(tags=["clinical"])
class VaccinationListView(generics.ListCreateAPIView):
    serializer_class = serializers.VaccinationSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "clinical.read"
    def get_queryset(self):
        qs = Vaccination.objects.for_tenant(self.request.tenant)
        pid = self.request.query_params.get("patient")
        if pid: qs = qs.filter(patient_id=pid)
        return qs
    def perform_create(self, s): s.save(tenant=self.request.tenant, administered_by=self.request.user)

@extend_schema(tags=["clinical"])
class HistoryListView(generics.ListCreateAPIView, views.APIView):
    """Family + Social history for a patient."""
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "clinical.read"
    def get(self, request):
        pid = request.query_params.get("patient")
        if not pid: return Response({"error":"patient required"}, status=400)
        family = FamilyHistory.objects.for_tenant(request.tenant).filter(patient_id=pid)
        social = SocialHistory.objects.for_tenant(request.tenant).filter(patient_id=pid).first()
        return Response({
            "family": serializers.FamilyHistorySerializer(family, many=True).data,
            "social": serializers.SocialHistorySerializer(social).data if social else None,
        })
    def post(self, request):
        stype = request.data.get("type")
        sdata = request.data.get("data", {})
        sdata["tenant"] = request.tenant
        if stype == "family":
            sdata["patient_id"] = request.data.get("patient_id")
            s = serializers.FamilyHistorySerializer(data=sdata)
            s.is_valid(raise_exception=True); s.save(tenant=request.tenant)
        elif stype == "social":
            sdata["patient_id"] = request.data.get("patient_id")
            sh, _ = SocialHistory.objects.get_or_create(tenant=request.tenant, patient_id=sdata["patient_id"])
            s = serializers.SocialHistorySerializer(sh, data=sdata, partial=True)
            s.is_valid(raise_exception=True); s.save()
        else: return Response({"error":"type must be family or social"}, status=400)
        return Response(s.data, status=201)

@extend_schema(tags=["clinical"])
class ClinicalDashboardView(views.APIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "clinical.read"
    def get(self, request):
        tenant = request.tenant; today = timezone.now().date()
        encounters_today = Encounter.objects.for_tenant(tenant).filter(encounter_date=today).count()
        pending_referrals = Referral.objects.for_tenant(tenant).filter(status="pending").count()
        return Response({"encounters_today":encounters_today,"pending_referrals":pending_referrals})
