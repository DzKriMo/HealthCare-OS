"""
Audit views — viewer with filtering, export to CSV/JSON.
"""
import csv
import io
import uuid
from django.http import HttpResponse
from rest_framework import generics, status, views
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from tenancy.permissions import HasTenantAccess, TenantPermissionRequired
from .models import AuditEvent
from . import serializers


@extend_schema(tags=["audit"])
class AuditEventListView(generics.ListAPIView):
    """
    List audit events with filtering.

    Filters: entity_type, entity_id, actor, action, date_from, date_to
    """
    serializer_class = serializers.AuditEventSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "audit.read"

    def get_queryset(self):
        qs = AuditEvent.objects.filter(tenant=self.request.tenant)

        entity_type = self.request.query_params.get("entity_type")
        if entity_type:
            qs = qs.filter(entity_type=entity_type)

        entity_id = self.request.query_params.get("entity_id")
        if entity_id:
            qs = qs.filter(entity_id=entity_id)

        actor_id = self.request.query_params.get("actor")
        if actor_id:
            qs = qs.filter(actor_id=actor_id)

        action = self.request.query_params.get("action")
        if action:
            qs = qs.filter(action=action)

        date_from = self.request.query_params.get("date_from")
        if date_from:
            qs = qs.filter(created_at__gte=date_from)

        date_to = self.request.query_params.get("date_to")
        if date_to:
            qs = qs.filter(created_at__lte=date_to)

        correlation_id = self.request.query_params.get("correlation_id")
        if correlation_id:
            qs = qs.filter(correlation_id=correlation_id)

        return qs.select_related("tenant", "actor")


@extend_schema(tags=["audit"], summary="Export audit log")
class AuditExportView(views.APIView):
    """
    Export audit events to CSV or JSON.

    GET /api/audit/export/?format=csv&date_from=2024-01-01
    """
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "audit.export"

    def get(self, request):
        query_serializer = serializers.AuditExportSerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        params = query_serializer.validated_data
        export_format = params.pop("format", "csv")

        qs = AuditEvent.objects.filter(tenant=request.tenant)

        if params.get("date_from"):
            qs = qs.filter(created_at__gte=params["date_from"])
        if params.get("date_to"):
            qs = qs.filter(created_at__lte=params["date_to"])
        if params.get("entity_type"):
            qs = qs.filter(entity_type=params["entity_type"])
        if params.get("action"):
            qs = qs.filter(action=params["action"])
        if params.get("actor_id"):
            qs = qs.filter(actor_id=params["actor_id"])

        qs = qs.values(
            "id", "actor_display", "entity_type", "entity_id",
            "action", "ip_address", "correlation_id", "created_at",
        )[:10000]  # Safety cap

        if export_format == "csv":
            return self._export_csv(qs)
        return self._export_json(qs)

    def _export_csv(self, queryset):
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Actor", "Entity Type", "Entity ID", "Action", "IP", "Correlation ID", "Timestamp"])
        for row in queryset:
            writer.writerow([
                str(row["id"]), row["actor_display"], row["entity_type"],
                row["entity_id"], row["action"], row["ip_address"] or "",
                str(row["correlation_id"]), str(row["created_at"]),
            ])
        response = HttpResponse(output.getvalue(), content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="audit_export.csv"'
        return response

    def _export_json(self, queryset):
        from django.core.serializers.json import DjangoJSONEncoder
        import json
        data = list(queryset)
        for row in data:
            for k, v in row.items():
                if hasattr(v, "isoformat"):
                    row[k] = v.isoformat()
                elif isinstance(v, uuid.UUID):
                    row[k] = str(v)
        response = HttpResponse(
            json.dumps(data, cls=DjangoJSONEncoder),
            content_type="application/json",
        )
        response["Content-Disposition"] = 'attachment; filename="audit_export.json"'
        return response
