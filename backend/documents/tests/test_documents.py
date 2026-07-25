"""Tests for document upload, list, and tenant isolation."""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from tenancy.models import Tenant
from identity.models import Role, Permission
from patients.models import Patient
from documents.models import Document

User = get_user_model()

@pytest.fixture
def tenant():
    return Tenant.objects.create(name="Test Clinic", slug="test-clinic")

@pytest.fixture
def perms():
    for c, d, r, a in [("documents.read","Read","documents","read"),("documents.upload","Upload","documents","upload"),("documents.delete","Delete","documents","delete"),("patients.read","P","patients","read")]:
        Permission.objects.get_or_create(codename=c, defaults={"description":d,"resource":r,"action":a})

@pytest.fixture
def role(tenant, perms):
    r = Role.objects.create(tenant=tenant, name="Doctor")
    r.permissions.add(*Permission.objects.filter(codename__startswith="documents"))
    r.permissions.add(Permission.objects.get(codename="patients.read"))
    return r

@pytest.fixture
def user(tenant, role):
    return User.objects.create_user(email="d@t.com", password="pass1234567890", first_name="J", last_name="D", tenant=tenant, role=role)

@pytest.fixture
def patient(tenant):
    return Patient.objects.create(tenant=tenant, first_name="A", last_name="S", display_id="P-001", date_of_birth="1990-01-01", phone_primary="+1", address_line1="A", city="X", country="US")

@pytest.fixture
def api_client():
    return APIClient()

def _auth(c, tenant_slug="test-clinic"):
    r = c.post("/api/auth/login/", {"email":"d@t.com","password":"pass1234567890","tenant_slug":tenant_slug}, format="json")
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {r.json()['tokens']['access']}", HTTP_X_TENANT_SLUG=tenant_slug)

@pytest.mark.django_db
class TestDocuments:
    def test_list_empty(self, api_client, user, tenant):
        _auth(api_client)
        resp = api_client.get("/api/documents/")
        assert resp.status_code == status.HTTP_200_OK

    def test_upload_and_download(self, api_client, user, patient, tenant):
        _auth(api_client)
        from django.core.files.uploadedfile import SimpleUploadedFile
        file_content = b"Hello, Healthcare OS!"
        upload = SimpleUploadedFile("test.pdf", file_content, content_type="application/pdf")
        resp = api_client.post("/api/documents/", {
            "file": upload, "patient_id": str(patient.id),
            "category": "consent", "description": "Test doc",
        }, format="multipart")
        assert resp.status_code == status.HTTP_201_CREATED
        data = resp.json()
        assert data["file_name"] == "test.pdf"
        assert data["category"] == "consent"
        assert "download_url" in data

    def test_tenant_isolation(self, api_client, user, tenant, patient):
        _auth(api_client)
        other = Tenant.objects.create(name="O", slug="other")
        doc = Document.objects.create(tenant=other, patient=patient, file_name="secret.pdf", file_size=100, mime_type="application/pdf", storage_path="other/secret.pdf")
        resp = api_client.get(f"/api/documents/{doc.id}/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND
