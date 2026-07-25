"""
Reporting and dashboard views — Sprint 6.

Reports: run operational/financial/clinical reports with parameters.
Dashboards: list widgets for user's role, fetch widget data.
"""
import datetime
import decimal
from django.utils import timezone
from django.db.models import Sum, Count, Q
from rest_framework import generics, status, views
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema

from tenancy.permissions import HasTenantAccess, TenantPermissionRequired
from .models import ReportDefinition, DashboardWidget
from . import serializers


# ═══════════════════════════════════════════════════════════════
# Reports
# ═══════════════════════════════════════════════════════════════

@extend_schema(tags=["reports"])
class ReportDefinitionListView(generics.ListAPIView):
    """List available report definitions."""
    serializer_class = serializers.ReportDefinitionSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "reports.view_operational"

    def get_queryset(self):
        return ReportDefinition.objects.filter(
            Q(tenant=self.request.tenant) | Q(tenant__isnull=True),
            is_active=True,
        )


@extend_schema(tags=["reports"], summary="Run a report")
class ReportRunView(generics.GenericAPIView):
    """
    Execute a report and return results.

    POST /api/reports/run/
    Body: {"report_type": "appointments_by_day", "date_from": "...", "date_to": "..."}
    """
    serializer_class = serializers.ReportRequestSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "reports.view_operational"

    def post(self, request):
        req_serializer = self.get_serializer(data=request.data)
        req_serializer.is_valid(raise_exception=True)
        params = req_serializer.validated_data

        report_type = params["report_type"]
        date_from = params.get("date_from")
        date_to = params.get("date_to")

        # Route to the appropriate report handler
        handler = getattr(self, f"_report_{report_type}", None)
        if handler is None:
            return Response(
                {"error": f"Unknown report type: {report_type}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        data = handler(request.tenant, date_from, date_to, params)
        return Response({
            "report_type": report_type,
            "generated_at": timezone.now().isoformat(),
            "parameters": params,
            "data": data,
        })

    def _report_appointments_by_day(self, tenant, date_from, date_to, params):
        """Appointments grouped by day."""
        from scheduling.models import Appointment
        qs = Appointment.objects.for_tenant(tenant)
        if date_from:
            qs = qs.filter(start_time__gte=date_from)
        if date_to:
            qs = qs.filter(start_time__lt=date_to)

        appointments = qs.values("start_time__date").annotate(
            total=Count("id"),
            completed=Count("id", filter=Q(status="completed")),
            cancelled=Count("id", filter=Q(status="cancelled")),
            no_show=Count("id", filter=Q(status="no_show")),
        ).order_by("start_time__date")

        return [{
            "date": str(a["start_time__date"]),
            "total": a["total"],
            "completed": a["completed"],
            "cancelled": a["cancelled"],
            "no_show": a["no_show"],
        } for a in appointments]

    def _report_no_show_rate(self, tenant, date_from, date_to, params):
        """No-show rate percentage."""
        from scheduling.models import Appointment
        qs = Appointment.objects.for_tenant(tenant)
        if date_from:
            qs = qs.filter(start_time__gte=date_from)
        if date_to:
            qs = qs.filter(start_time__lt=date_to)

        total = qs.count()
        no_shows = qs.filter(status="no_show").count()
        rate = round((no_shows / total * 100), 1) if total > 0 else 0

        return {"total_appointments": total, "no_shows": no_shows, "rate_pct": rate}

    def _report_revenue_summary(self, tenant, date_from, date_to, params):
        """Revenue summary for the period."""
        from billing.models import Payment
        qs = Payment.objects.for_tenant(tenant).filter(is_refund=False)
        if date_from:
            qs = qs.filter(payment_date__gte=date_from)
        if date_to:
            qs = qs.filter(payment_date__lt=date_to)

        total = qs.aggregate(t=Sum("amount"))["t"] or decimal.Decimal("0")
        by_method = qs.values("method").annotate(total=Sum("amount")).order_by("-total")

        return {
            "total_revenue": str(total),
            "by_method": [{"method": m["method"], "total": str(m["total"])} for m in by_method],
        }

    def _report_patient_registrations(self, tenant, date_from, date_to, params):
        """New patient registrations over time."""
        from patients.models import Patient
        qs = Patient.objects.for_tenant(tenant)
        if date_from:
            qs = qs.filter(registration_date__gte=date_from)
        if date_to:
            qs = qs.filter(registration_date__lt=date_to)

        registrations = qs.values("registration_date").annotate(
            count=Count("id"),
        ).order_by("registration_date")

        return [{
            "date": str(r["registration_date"]),
            "count": r["count"],
        } for r in registrations]

    def _report_outstanding_balances(self, tenant, date_from, date_to, params):
        """Invoices with outstanding balances."""
        from billing.models import Invoice
        qs = Invoice.objects.for_tenant(tenant).filter(
            balance_due__gt=0,
        ).exclude(status__in=["cancelled", "void"])

        total_os = qs.aggregate(t=Sum("balance_due"))["t"] or decimal.Decimal("0")

        return {
            "total_outstanding": str(total_os),
            "invoice_count": qs.count(),
        }


# ═══════════════════════════════════════════════════════════════
# Dashboards
# ═══════════════════════════════════════════════════════════════

@extend_schema(tags=["reports"])
class DashboardWidgetListView(generics.ListCreateAPIView):
    """List or create dashboard widgets for the tenant."""
    serializer_class = serializers.DashboardWidgetSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "reports.view_operational"

    def get_queryset(self):
        return DashboardWidget.objects.for_tenant(self.request.tenant).filter(is_active=True)

    def perform_create(self, serializer):
        serializer.save(tenant=self.request.tenant)


@extend_schema(tags=["reports"], summary="Get dashboard data")
class DashboardDataView(generics.GenericAPIView):
    """
    Fetch data for all visible dashboard widgets for the current user.

    GET /api/reports/dashboard/
    """
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "reports.view_operational"

    def get(self, request):
        user = request.user
        role = user.role

        # Get widgets visible to this role
        widgets = DashboardWidget.objects.for_tenant(request.tenant).filter(
            is_active=True,
        ).filter(
            Q(roles=role) | Q(roles__isnull=True),
        )

        widget_data = []
        for widget in widgets:
            data = self._fetch_widget_data(widget, request.tenant)
            widget_data.append({
                "widget_id": str(widget.id),
                "widget_type": widget.widget_type,
                "title": widget.title or widget.get_widget_type_display(),
                "data": data,
                "refreshed_at": timezone.now().isoformat(),
            })

        return Response({"widgets": widget_data})

    def _fetch_widget_data(self, widget, tenant) -> dict:
        """Fetch data for a specific widget type."""
        handlers = {
            "appointments_today": self._widget_appointments_today,
            "revenue_today": self._widget_revenue_today,
            "new_patients": self._widget_new_patients,
            "pending_invoices": self._widget_pending_invoices,
            "low_stock": self._widget_low_stock,
            "queue_status": self._widget_queue_status,
        }
        handler = handlers.get(widget.widget_type, lambda t: {"value": "—"})
        return handler(tenant)

    def _widget_appointments_today(self, tenant):
        from scheduling.models import Appointment
        today = timezone.now().date()
        count = Appointment.objects.for_tenant(tenant).filter(
            start_time__date=today,
        ).exclude(status="cancelled").count()
        return {"count": count, "label": "Today's Appointments"}

    def _widget_revenue_today(self, tenant):
        from billing.models import Payment
        today = timezone.now().date()
        total = Payment.objects.for_tenant(tenant).filter(
            is_refund=False, payment_date__date=today,
        ).aggregate(t=Sum("amount"))["t"] or 0
        return {"amount": str(total), "label": "Today's Revenue"}

    def _widget_new_patients(self, tenant):
        from patients.models import Patient
        this_month = timezone.now().date().replace(day=1)
        count = Patient.objects.for_tenant(tenant).filter(
            registration_date__gte=this_month,
        ).count()
        return {"count": count, "label": "New Patients This Month"}

    def _widget_pending_invoices(self, tenant):
        from billing.models import Invoice
        qs = Invoice.objects.for_tenant(tenant).filter(balance_due__gt=0).exclude(
            status__in=["cancelled", "void"],
        )
        total = qs.aggregate(t=Sum("balance_due"))["t"] or 0
        return {"count": qs.count(), "total": str(total), "label": "Pending Invoices"}

    def _widget_low_stock(self, tenant):
        return {"count": 0, "label": "Low Stock Items", "note": "Inventory module pending"}

    def _widget_queue_status(self, tenant):
        from scheduling.models import Appointment
        today = timezone.now().date()
        counts = Appointment.objects.for_tenant(tenant).filter(
            start_time__date=today,
        ).values("status").annotate(count=Count("id"))
        return {
            "by_status": {c["status"]: c["count"] for c in counts},
            "label": "Queue Status",
        }
