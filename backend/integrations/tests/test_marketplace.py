import pytest; from django.contrib.auth import get_user_model; from rest_framework.test import APIClient; from rest_framework import status
from tenancy.models import Tenant; from identity.models import Role, Permission
from integrations.models import Plugin, PluginInstallation, PluginReview

User = get_user_model()

@pytest.fixture
def tenant(db):
    t = Tenant.objects.create(name="TC", slug="mc")
    Permission.objects.get_or_create(codename="integrations.manage", defaults={"description":"M","resource":"integrations","action":"manage"})
    role = Role.objects.create(tenant=t, name="Admin")
    role.permissions.add(Permission.objects.get(codename="integrations.manage"))
    User.objects.create_user(email="a@mc.com", password="pass1234567890", first_name="A", last_name="U", tenant=t, role=role)
    # Create a sample plugin
    Plugin.objects.create(name="WhatsApp Connector", slug="whatsapp-connector", version="1.0.0", author="Healthcare OS Labs",
                          description="Send WhatsApp notifications.", category="communication", is_published=True, is_certified=True)
    return t

@pytest.fixture
def api_client(): return APIClient()

def _auth(c):
    r = c.post("/api/auth/login/", {"email":"a@mc.com","password":"pass1234567890","tenant_slug":"mc"}, format="json")
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {r.json()['tokens']['access']}", HTTP_X_TENANT_SLUG="mc")

@pytest.mark.django_db
class TestMarketplace:
    def test_catalog(self, api_client, tenant):
        _auth(api_client)
        resp = api_client.get("/api/integrations/marketplace/")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.json()) >= 1

    def test_install_plugin(self, api_client, tenant):
        _auth(api_client)
        plugin = Plugin.objects.first()
        resp = api_client.post("/api/integrations/marketplace/installed/", {"plugin_id":str(plugin.id)}, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json()["is_enabled"] is True

    def test_list_installed(self, api_client, tenant):
        _auth(api_client)
        plugin = Plugin.objects.first()
        PluginInstallation.objects.create(tenant=tenant, plugin=plugin, installed_version="1.0.0")
        resp = api_client.get("/api/integrations/marketplace/installed/")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.json()) >= 1

    def test_review(self, api_client, tenant):
        _auth(api_client)
        plugin = Plugin.objects.first()
        resp = api_client.post(f"/api/integrations/marketplace/{plugin.id}/reviews/", {"rating":5,"title":"Great plugin!","body":"Works perfectly."}, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        plugin.refresh_from_db()
        assert plugin.average_rating == 5.0
