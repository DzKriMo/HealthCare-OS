"""Tests for imaging module."""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from tenancy.models import Tenant
from identity.models import Role, Permission
from patients.models import Patient

User = get_user_model()

@pytest.fixture
def tenant(): return Tenant.objects.create(name="TC", slug="tc")

@pytest.fixture
def perms():
    for c,d,r,a in [("imaging.read","R","imaging","read"),("imaging.upload","U","imaging","upload"),
                     ("imaging.report","Re","imaging","report"),("imaging.sign","S","imaging","sign"),
                     ("patients.read","R","patients","read")]:
        Permission.objects.get_or_create(codename=c, defaults={"description":d,"resource":r,"action":a})

@pytest.fixture
def role(tenant, perms):
    r = Role.objects.create(tenant=tenant, name="Radiologist")
    r.permissions.add(*Permission.objects.filter(codename__startswith="imaging"))
    r.permissions.add(Permission.objects.get(codename="patients.read"))
    return r

@pytest.fixture
def user(tenant, role):
    return User.objects.create_user(email="rad@t.com", password="pass1234567890", first_name="Rad", last_name="User", tenant=tenant, role=role)

@pytest.fixture
def patient(tenant):
    return Patient.objects.create(tenant=tenant, first_name="P", last_name="T", display_id="P-01", date_of_birth="1990-01-01", phone_primary="+1", address_line1="A", city="X", country="US")

@pytest.fixture
def api_client(): return APIClient()

def _auth(c):
    r = c.post("/api/auth/login/", {"email":"rad@t.com","password":"pass1234567890","tenant_slug":"tc"}, format="json")
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {r.json()['tokens']['access']}", HTTP_X_TENANT_SLUG="tc")

@pytest.mark.django_db
class TestImaging:
    def test_create_study(self, api_client, user, patient, tenant):
        _auth(api_client)
        resp = api_client.post("/api/imaging/studies/", {
            "patient":str(patient.id),"modality":"xray","body_part":"Chest","priority":"routine",
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json()["modality"] == "xray"

    def test_create_report(self, api_client, user, patient, tenant):
        _auth(api_client)
        from imaging.models import ImagingStudy
        study = ImagingStudy.objects.create(tenant=tenant, patient=patient, modality="xray", body_part="Chest",
                                            study_uid="1.2.840.test")
        resp = api_client.post("/api/imaging/reports/", {
            "study":str(study.id),"findings":"Normal","impression":"Clear","recommendations":"None",
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED

    def test_sign_report(self, api_client, user, patient, tenant):
        _auth(api_client)
        from imaging.models import ImagingStudy, RadiologyReport
        study = ImagingStudy.objects.create(tenant=tenant, patient=patient, modality="mri", body_part="Brain",
                                            study_uid="1.2.840.test2")
        report = RadiologyReport.objects.create(tenant=tenant, study=study, author=user, findings="Normal")
        resp = api_client.post(f"/api/imaging/reports/{report.id}/sign/")
        assert resp.status_code == status.HTTP_200_OK
        report.refresh_from_db(); study.refresh_from_db()
        assert report.status == "signed"
        assert study.status == "completed"

    def test_dashboard(self, api_client, user, tenant):
        _auth(api_client)
        resp = api_client.get("/api/imaging/dashboard/")
        assert resp.status_code == status.HTTP_200_OK
        assert "studies_today" in resp.json()
