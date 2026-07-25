from django.db import models as db_models
from rest_framework import generics, status
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from tenancy.permissions import HasTenantAccess, TenantPermissionRequired
from .models import AISettings, AISuggestion, AIAuditLog
from . import serializers
from .services import AIDiagnosticsService


@extend_schema(tags=["ai-diagnostics"])
class AISettingsView(generics.RetrieveUpdateAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    serializer_class = serializers.AISettingsSerializer

    def get_required_permission(self):
        return "ai_diagnostics.manage"

    def get_object(self):
        obj, _ = AISettings.objects.get_or_create(tenant=self.request.tenant)
        return obj


@extend_schema(tags=["ai-diagnostics"])
class ICD10SuggestView(generics.GenericAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    serializer_class = serializers.ICD10SuggestionInputSerializer

    def get_required_permission(self):
        return "ai_diagnostics.use"

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = AIDiagnosticsService(request.tenant)
        result = service.suggest_icd10(
            serializer.validated_data["diagnosis_text"],
            serializer.validated_data.get("context"),
        )
        return Response(result)


@extend_schema(tags=["ai-diagnostics"])
class SOAPDraftView(generics.GenericAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    serializer_class = serializers.SOAPDraftInputSerializer

    def get_required_permission(self):
        return "ai_diagnostics.use"

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = AIDiagnosticsService(request.tenant)
        result = service.draft_soap(serializer.validated_data)
        return Response(result)


@extend_schema(tags=["ai-diagnostics"])
class DrugInteractionView(generics.GenericAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    serializer_class = serializers.DrugInteractionInputSerializer

    def get_required_permission(self):
        return "ai_diagnostics.use"

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = AIDiagnosticsService(request.tenant)
        result = service.check_drug_interaction(serializer.validated_data["medications"])
        return Response(result)


@extend_schema(tags=["ai-diagnostics"])
class SymptomAnalysisView(generics.GenericAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    serializer_class = serializers.SymptomAnalysisInputSerializer

    def get_required_permission(self):
        return "ai_diagnostics.use"

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = AIDiagnosticsService(request.tenant)
        result = service.analyze_symptoms(
            serializer.validated_data["symptoms"],
            serializer.validated_data.get("vitals"),
        )
        return Response(result)


@extend_schema(tags=["ai-diagnostics"])
class TreatmentPlanView(generics.GenericAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    serializer_class = serializers.TreatmentPlanInputSerializer

    def get_required_permission(self):
        return "ai_diagnostics.use"

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = AIDiagnosticsService(request.tenant)
        result = service.suggest_treatment_plan(
            serializer.validated_data["diagnosis"],
            serializer.validated_data.get("patient_info"),
        )
        return Response(result)


@extend_schema(tags=["ai-diagnostics"])
class CPTSuggestView(generics.GenericAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    serializer_class = serializers.CPTInputSerializer

    def get_required_permission(self):
        return "ai_diagnostics.use"

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = AIDiagnosticsService(request.tenant)
        result = service.suggest_cpt_codes(serializer.validated_data["procedure_description"])
        return Response(result)


@extend_schema(tags=["ai-diagnostics"])
class PrescriptionDraftView(generics.GenericAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    serializer_class = serializers.PrescriptionDraftInputSerializer

    def get_required_permission(self):
        return "ai_diagnostics.use"

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = AIDiagnosticsService(request.tenant)
        result = service.draft_prescription(
            serializer.validated_data["diagnosis"],
            serializer.validated_data.get("patient_info"),
        )
        return Response(result)


@extend_schema(tags=["ai-diagnostics"])
class SuggestionFeedbackView(generics.GenericAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    serializer_class = serializers.SuggestionFeedbackSerializer

    def get_required_permission(self):
        return "ai_diagnostics.use"

    def post(self, request, pk):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        service = AIDiagnosticsService(request.tenant)
        if serializer.validated_data["accepted"]:
            result = service.accept_suggestion(pk, request.user)
        else:
            result = service.reject_suggestion(pk, request.user)
        return Response(result)


@extend_schema(tags=["ai-diagnostics"])
class SuggestionListView(generics.ListAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    serializer_class = serializers.AISuggestionSerializer

    def get_required_permission(self):
        return "ai_diagnostics.read"

    def get_queryset(self):
        qs = AISuggestion.objects.for_tenant(self.request.tenant)
        suggestion_type = self.request.query_params.get("type")
        if suggestion_type:
            qs = qs.filter(suggestion_type=suggestion_type)
        patient = self.request.query_params.get("patient")
        if patient:
            qs = qs.filter(patient_id=patient)
        accepted = self.request.query_params.get("accepted")
        if accepted == "true":
            qs = qs.filter(accepted=True)
        elif accepted == "false":
            qs = qs.filter(accepted=False)
        return qs


@extend_schema(tags=["ai-diagnostics"])
class AuditLogListView(generics.ListAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    serializer_class = serializers.AIAuditLogSerializer

    def get_required_permission(self):
        return "ai_diagnostics.audit"

    def get_queryset(self):
        return AIAuditLog.objects.for_tenant(self.request.tenant).select_related("user", "suggestion")


@extend_schema(tags=["ai-diagnostics"])
class DashboardView(generics.GenericAPIView):
    permission_classes = [HasTenantAccess, TenantPermissionRequired]

    def get_required_permission(self):
        return "ai_diagnostics.read"

    def get(self, request):
        qs = AISuggestion.objects.for_tenant(request.tenant)
        return Response({
            "total_suggestions": qs.count(),
            "accepted": qs.filter(accepted=True).count(),
            "rejected": qs.filter(accepted=False).count(),
            "pending_review": qs.filter(accepted__isnull=True).count(),
            "fallback_rate": qs.filter(is_fallback=True).count(),
            "avg_latency_ms": qs.exclude(latency_ms__isnull=True).aggregate(
                avg=db_models.Avg("latency_ms")
            )["avg_latency_ms"],
        })
