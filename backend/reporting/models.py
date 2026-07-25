"""
Reporting and dashboard models — Sprint 6.

Report definitions with parameterized queries. Dashboard widgets
that are tenant, role, and module aware.
"""
import uuid
from django.db import models
from tenancy.models import Tenant
from tenancy.managers import TenantScopedManager


class ReportDefinition(models.Model):
    """
    A defined report with query template and configurable parameters.

    Reports can be operational, financial, or clinical. Parameters
    allow filtering by date range, practitioner, etc.
    """

    class Category(models.TextChoices):
        OPERATIONAL = "operational", "Operational"
        FINANCIAL = "financial", "Financial"
        CLINICAL = "clinical", "Clinical"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="report_definitions",
        null=True, blank=True,
        help_text="Null for built-in reports available to all tenants.",
    )
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.OPERATIONAL)

    # Query definition (conceptual — executed in views)
    report_type = models.CharField(
        max_length=100,
        help_text="Identifier for the report logic, e.g. 'appointments_by_day'.",
    )
    parameters_schema = models.JSONField(
        default=dict,
        help_text="JSON Schema for report parameters: date_from, date_to, practitioner_id, etc.",
    )

    # Permissions
    required_permission = models.CharField(
        max_length=100, blank=True,
        help_text="Permission required to run this report.",
    )
    module_dependency = models.CharField(
        max_length=50, blank=True,
        help_text="Module that must be enabled, e.g. 'dental'.",
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "reporting_report_definition"
        ordering = ["category", "name"]

    def __str__(self):
        return f"{self.name} ({self.category})"


class DashboardWidget(models.Model):
    """
    A dashboard widget — configurable per tenant and role.

    Widgets are registered by modules or created by tenant admins.
    The frontend renders them based on the user's role and enabled modules.
    """

    class WidgetType(models.TextChoices):
        APPOINTMENTS_TODAY = "appointments_today", "Today's Appointments"
        REVENUE_TODAY = "revenue_today", "Today's Revenue"
        NEW_PATIENTS = "new_patients", "New Patients This Month"
        PENDING_INVOICES = "pending_invoices", "Pending Invoices"
        LOW_STOCK = "low_stock", "Low Stock Alerts"
        QUEUE_STATUS = "queue_status", "Queue Status"
        PROCEDURE_MIX = "procedure_mix", "Procedure Mix"
        NO_SHOW_RATE = "no_show_rate", "No-Show Rate"
        CUSTOM = "custom", "Custom"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name="dashboard_widgets",
    )

    widget_type = models.CharField(max_length=30, choices=WidgetType.choices)
    title = models.CharField(max_length=200, blank=True)
    config = models.JSONField(default=dict, help_text="Widget-specific configuration.")

    # Layout
    position_x = models.IntegerField(default=0)
    position_y = models.IntegerField(default=0)
    width = models.IntegerField(default=1, help_text="Grid columns (1-4).")
    height = models.IntegerField(default=1)

    # Visibility
    roles = models.ManyToManyField(
        "identity.Role", blank=True,
        help_text="Roles that can see this widget. Empty = all roles.",
    )
    module_dependency = models.CharField(
        max_length=50, blank=True,
        help_text="Only show if this module is enabled.",
    )
    required_permission = models.CharField(max_length=100, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    objects = TenantScopedManager()

    class Meta:
        db_table = "reporting_dashboard_widget"
        ordering = ["position_y", "position_x"]

    def __str__(self):
        return f"{self.title or self.widget_type} ({self.tenant})"
