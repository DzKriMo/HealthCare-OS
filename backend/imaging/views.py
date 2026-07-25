"""Imaging views — studies, series, images, reports."""
from django.utils import timezone
from django.db import models as db_models
from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.exceptions import NotFound
from drf_spectacular.utils import extend_schema
from tenancy.permissions import HasTenantAccess, TenantPermissionRequired
from .models import ImagingStudy, ImagingSeries, ImagingImage, RadiologyReport
from . import serializers


@extend_schema(tags=["imaging"])
class StudyListView(generics.ListCreateAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    def get_serializer_class(self):
        return serializers.StudyCreateSerializer if self.request.method == "POST" else serializers.ImagingStudyListSerializer
    def get_queryset(self):
        qs = ImagingStudy.objects.for_tenant(self.request.tenant).select_related("patient").prefetch_related("report")
        pid = self.request.query_params.get("patient")
        if pid: qs = qs.filter(patient_id=pid)
        return qs
    def get_required_permission(self):
        return "imaging.upload" if self.request.method == "POST" else "imaging.read"


@extend_schema(tags=["imaging"])
class StudyDetailView(generics.RetrieveAPIView):
    serializer_class = serializers.ImagingStudyListSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "imaging.read"
    def get_queryset(self): return ImagingStudy.objects.for_tenant(self.request.tenant)


@extend_schema(tags=["imaging"])
class ReportListView(generics.ListCreateAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    def get_serializer_class(self):
        return serializers.ReportCreateSerializer if self.request.method == "POST" else serializers.RadiologyReportSerializer
    def get_queryset(self):
        return RadiologyReport.objects.for_tenant(self.request.tenant).select_related("study","author","signed_by")
    def get_required_permission(self):
        return "imaging.report" if self.request.method == "POST" else "imaging.read"


@extend_schema(tags=["imaging"])
class ReportSignView(views.APIView):
    """Sign a radiology report."""
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "imaging.sign"
    def post(self, request, pk):
        try: r = RadiologyReport.objects.for_tenant(request.tenant).get(pk=pk)
        except RadiologyReport.DoesNotExist: return Response({"error":"Not found"}, status=404)
        if r.status == RadiologyReport.Status.SIGNED:
            return Response({"error":"Already signed"}, status=400)
        r.status = RadiologyReport.Status.SIGNED
        r.signed_by = request.user; r.signed_at = timezone.now()
        r.save()
        r.study.status = ImagingStudy.Status.COMPLETED
        r.study.save(update_fields=["status"])
        return Response(serializers.RadiologyReportSerializer(r).data)


@extend_schema(tags=["imaging"])
class ImagingDashboardView(views.APIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "imaging.read"
    def get(self, request):
        tenant = request.tenant
        today = timezone.now().date()
        studies_today = ImagingStudy.objects.for_tenant(tenant).filter(performed_at__date=today).count()
        pending_reports = RadiologyReport.objects.for_tenant(tenant).exclude(status__in=["signed","amended"]).count()
        by_modality = list(ImagingStudy.objects.for_tenant(tenant).values("modality").annotate(c=db_models.Count("id")))
        return Response({"studies_today":studies_today,"pending_reports":pending_reports,"by_modality":by_modality})
