"""Tests for lab module."""
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
    for c,d,r,a in [("lab.read","R","lab","read"),("lab.order","O","lab","order"),("lab.collect","C","lab","collect"),
                     ("lab.result","Re","lab","result"),("lab.approve","A","lab","approve"),("patients.read","R","patients","read")]:
        Permission.objects.get_or_create(codename=c, defaults={"description":d,"resource":r,"action":a})

@pytest.fixture
def role(tenant, perms):
    r = Role.objects.create(tenant=tenant, name="LabTech")
    r.permissions.add(*Permission.objects.filter(codename__startswith="lab"))
    r.permissions.add(Permission.objects.get(codename="patients.read"))
    return r

@pytest.fixture
def user(tenant, role):
    return User.objects.create_user(email="lab@t.com", password="pass1234567890", first_name="L", last_name="T", tenant=tenant, role=role)

@pytest.fixture
def patient(tenant):
    return Patient.objects.create(tenant=tenant, first_name="P", last_name="T", display_id="P-01", date_of_birth="1990-01-01", phone_primary="+1", address_line1="A", city="X", country="US")

@pytest.fixture
def api_client(): return APIClient()

def _auth(c):
    r = c.post("/api/auth/login/", {"email":"lab@t.com","password":"pass1234567890","tenant_slug":"tc"}, format="json")
    c.credentials(HTTP_AUTHORIZATION=f"Bearer {r.json()['tokens']['access']}", HTTP_X_TENANT_SLUG="tc")

def _create_test(api_client):
    return api_client.post("/api/lab/catalog/", {"name":"CBC","department":"hematology","specimen_type":"Blood","unit":"x10^9/L","reference_range_low":"4.0","reference_range_high":"11.0","price":"25.00"}, format="json")

@pytest.mark.django_db
class TestLabFull:
    def test_catalog_crud(self, api_client, user, tenant):
        _auth(api_client)
        resp = _create_test(api_client)
        assert resp.status_code == status.HTTP_201_CREATED

    def test_order_workflow(self, api_client, user, patient, tenant):
        _auth(api_client)
        tr = _create_test(api_client)
        test_id = tr.json()["id"]
        resp = api_client.post("/api/lab/orders/", {"patient":str(patient.id),"test_ids":[test_id],"priority":"routine"}, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        order_id = resp.json()["id"]

        # Collect specimen
        sr = api_client.post("/api/lab/specimens/", {"lab_order":order_id,"specimen_type":"Blood"}, format="json")
        assert sr.status_code == status.HTTP_201_CREATED
        assert sr.json()["barcode"].startswith("SPC-")
        spec_id = sr.json()["id"]

        # Transition specimen through lifecycle
        for target in ["received","processing","completed"]:
            tr = api_client.post(f"/api/lab/specimens/{spec_id}/transition/", {"status":target}, format="json")
            assert tr.status_code == status.HTTP_200_OK

        # Enter result
        rr = api_client.post("/api/lab/results/", {"lab_order":order_id,"test":test_id,"value":"15.5"}, format="json")
        assert rr.status_code == status.HTTP_201_CREATED
        assert rr.json()["flag"] == "high"
        result_id = rr.json()["id"]

        # Approve
        r1 = api_client.post(f"/api/lab/results/{result_id}/approve/", {"action":"review"}, format="json")
        assert r1.status_code == status.HTTP_200_OK
        r2 = api_client.post(f"/api/lab/results/{result_id}/approve/", {"action":"approve"}, format="json")
        assert r2.status_code == status.HTTP_200_OK

    def test_dashboard(self, api_client, user, tenant):
        _auth(api_client)
        resp = api_client.get("/api/lab/dashboard/")
        assert resp.status_code == status.HTTP_200_OK
        assert "pending_results" in resp.json()

    def test_reject_specimen(self, api_client, user, patient, tenant):
        _auth(api_client)
        tr = _create_test(api_client)
        resp = api_client.post("/api/lab/orders/", {"patient":str(patient.id),"test_ids":[tr.json()["id"]],"priority":"routine"}, format="json")
        sr = api_client.post("/api/lab/specimens/", {"lab_order":resp.json()["id"],"specimen_type":"Blood"}, format="json")
        spec_id = sr.json()["id"]
        rr = api_client.post(f"/api/lab/specimens/{spec_id}/transition/", {"status":"rejected","reason":"Hemolyzed"}, format="json")
        assert rr.status_code == status.HTTP_200_OK
        assert rr.json()["status"] == "rejected"
