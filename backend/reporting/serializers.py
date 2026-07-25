"""Serializers for reports and dashboards."""
from rest_framework import serializers
from .models import ReportDefinition, DashboardWidget


class ReportDefinitionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReportDefinition
        fields = [
            "id", "name", "description", "category", "report_type",
            "parameters_schema", "required_permission", "module_dependency",
        ]
        read_only_fields = ["id"]


class ReportRequestSerializer(serializers.Serializer):
    """Request parameters for running a report."""
    report_type = serializers.CharField()
    date_from = serializers.DateField(required=False)
    date_to = serializers.DateField(required=False)
    practitioner_id = serializers.UUIDField(required=False)
    format = serializers.ChoiceField(choices=["json", "csv"], default="json")


class DashboardWidgetSerializer(serializers.ModelSerializer):
    class Meta:
        model = DashboardWidget
        fields = [
            "id", "widget_type", "title", "config",
            "position_x", "position_y", "width", "height",
            "roles", "module_dependency", "required_permission",
            "is_active",
        ]
        read_only_fields = ["id"]


class DashboardDataSerializer(serializers.Serializer):
    """Response format for dashboard widget data."""
    widget_id = serializers.UUIDField()
    widget_type = serializers.CharField()
    title = serializers.CharField()
    data = serializers.JSONField()
    refreshed_at = serializers.DateTimeField()
