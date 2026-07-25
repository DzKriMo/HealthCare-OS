"""Tests for reports and dashboards."""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from tenancy.models import Tenant
from identity.models import Role, Permission
from reporting.models import ReportDefinition, DashboardWidget

User = get_user_model()

@pytest.fixture
def tenant():
    return Tenant.objects.create(name="TC", slug="tc")

@pytest.fixture
def perms():
    for c, d, r, a in [("reports.view_operational","V","reports","view_operational")]:
        Permission.objects.get_or_create(codename=c, defaults={"description":d,"resource":r,"action":a})

@pytest.fixture
def role(tenant, perms):
    r = Role.objects.create(tenant=tenant, name="Manager")
    r.permissions.add(*Permission.objects.filter(codename__startswith="reports"))
    return r

@pytest.fixture
def user(tenant, role):
    return User.objects.create_user(email="m@t.com", password="pass1234567890", first_name="M", last_name="U", tenant=tenant, role=role)

@pytest.fixture
def api_client():
    return APIClient()

def _auth(c):
    r = c.post("/api/auth/login/", {"email":"m@t.com","password":"pass1234567890","tenant_slug":"tc"}, format="json")
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {r.json()['tokens']['access']}", HTTP_X_TENANT_SLUG="tc")

@pytest.mark.django_db
class TestReports:
    def test_list_definitions(self, api_client, user, tenant):
        _auth(api_client)
        ReportDefinition.objects.create(tenant=tenant, name="Test Report", report_type="appointments_by_day")
        resp = api_client.get("/api/reports/definitions/")
        assert resp.status_code == status.HTTP_200_OK

    def test_run_appointments_report(self, api_client, user, tenant):
        _auth(api_client)
        resp = api_client.post("/api/reports/run/", {
            "report_type": "appointments_by_day",
        }, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert "data" in resp.json()

    def test_run_revenue_report(self, api_client, user, tenant):
        _auth(api_client)
        resp = api_client.post("/api/reports/run/", {
            "report_type": "revenue_summary",
        }, format="json")
        assert resp.status_code == status.HTTP_200_OK

    def test_run_no_show_report(self, api_client, user, tenant):
        _auth(api_client)
        resp = api_client.post("/api/reports/run/", {
            "report_type": "no_show_rate",
        }, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert "rate_pct" in resp.json()["data"]

    def test_dashboard_data(self, api_client, user, tenant):
        _auth(api_client)
        DashboardWidget.objects.create(tenant=tenant, widget_type="appointments_today")
        resp = api_client.get("/api/reports/dashboard/")
        assert resp.status_code == status.HTTP_200_OK
        assert "widgets" in resp.json()

    def test_dashboard_widget_crud(self, api_client, user, tenant):
        _auth(api_client)
        resp = api_client.post("/api/reports/widgets/", {
            "widget_type": "appointments_today",
            "title": "Today's Appts",
            "width": 2, "height": 1,
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
