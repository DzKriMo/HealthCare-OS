from django.contrib import admin
from .models import ReportDefinition, DashboardWidget

@admin.register(ReportDefinition)
class ReportDefinitionAdmin(admin.ModelAdmin):
    list_display = ["name", "category", "report_type", "tenant", "is_active"]

@admin.register(DashboardWidget)
class DashboardWidgetAdmin(admin.ModelAdmin):
    list_display = ["title", "widget_type", "tenant", "is_active"]
    list_filter = ["widget_type", "tenant"]
