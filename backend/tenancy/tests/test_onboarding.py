"""Tests for onboarding wizard, editions, and compliance."""
import pytest; from django.contrib.auth import get_user_model; from rest_framework.test import APIClient; from rest_framework import status
from tenancy.models import Tenant, ProductEdition, CompliancePolicy, OnboardingStep
from identity.models import Role, Permission

User = get_user_model()

@pytest.fixture
def tenant(db):
    t = Tenant.objects.create(name="TC", slug="tc")
    Permission.objects.get_or_create(codename="identity.manage_tenant", defaults={"description":"M","resource":"identity","action":"manage_tenant"})
    role = Role.objects.create(tenant=t, name="Admin")
    role.permissions.add(Permission.objects.get(codename="identity.manage_tenant"))
    User.objects.create_user(email="a@tc.com", password="pass1234567890", first_name="A", last_name="U", tenant=t, role=role)
    return t

@pytest.fixture
def api_client(): return APIClient()

def _auth(c):
    r = c.post("/api/auth/login/", {"email":"a@tc.com","password":"pass1234567890","tenant_slug":"tc"}, format="json")
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {r.json()['tokens']['access']}", HTTP_X_TENANT_SLUG="tc")

@pytest.mark.django_db
class TestOnboarding:
    def test_onboarding_status(self, api_client, tenant):
        _auth(api_client)
        resp = api_client.get("/api/onboarding/")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["total"] == 8  # Default steps
        assert "steps" in data

    def test_complete_step(self, api_client, tenant):
        _auth(api_client)
        api_client.get("/api/onboarding/")  # Initialize steps
        resp = api_client.post("/api/onboarding/", {"step_name":"clinic_info"}, format="json")
        assert resp.status_code == status.HTTP_200_OK
        assert resp.json()["completed"] is True

    def test_editions(self, api_client, tenant):
        _auth(api_client)
        ProductEdition.objects.create(name="solo", max_users=5, max_branches=1, monthly_price=99,
                                      enabled_modules=["dental","billing"])
        resp = api_client.get("/api/editions/")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.json()) >= 1

    def test_compliance_policy(self, tenant):
        policy = CompliancePolicy.objects.create(tenant=tenant)
        assert policy.clinical_record_retention_days == 3650
        assert policy.require_signature_on_prescriptions is True

    def test_product_edition_features(self):
        edition = ProductEdition.objects.create(name="hospital", max_users=100, max_branches=10, monthly_price=999,
                                                features={"telehealth":True,"ai_assistant":True,"fhir_api":True,"white_label":True})
        assert edition.features["fhir_api"] is True
