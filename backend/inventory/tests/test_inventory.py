"""Tests for inventory — items, stock movements, suppliers, POs, batches."""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status
from tenancy.models import Tenant
from identity.models import Role, Permission
from inventory.models import InventoryItem, Supplier, PurchaseOrder, StockMovement, Batch

User = get_user_model()

@pytest.fixture
def tenant():
    return Tenant.objects.create(name="TC", slug="tc")

@pytest.fixture
def perms():
    for c, d, r, a in [
        ("inventory.read","R","inventory","read"),
        ("inventory.adjust_stock","A","inventory","adjust"),
        ("inventory.manage_suppliers","S","inventory","suppliers"),
        ("inventory.create_po","P","inventory","create_po"),
        ("inventory.receive_po","R","inventory","receive_po"),
        ("inventory.manage_batches","B","inventory","batches"),
    ]:
        Permission.objects.get_or_create(codename=c, defaults={"description":d,"resource":r,"action":a})

@pytest.fixture
def role(tenant, perms):
    r = Role.objects.create(tenant=tenant, name="Manager")
    r.permissions.add(*Permission.objects.filter(codename__startswith="inventory"))
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
class TestInventoryItems:
    def test_create_item(self, api_client, user, tenant):
        _auth(api_client)
        resp = api_client.post("/api/inventory/items/", {
            "name": "Surgical Mask", "category": "supply", "unit": "box",
            "reorder_point": "50", "reorder_quantity": "200",
            "unit_cost": "5.00", "unit_price": "12.00",
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json()["name"] == "Surgical Mask"

    def test_list_items(self, api_client, user, tenant):
        _auth(api_client)
        InventoryItem.objects.create(tenant=tenant, name="Gloves", category="supply", unit="box", reorder_point=10)
        resp = api_client.get("/api/inventory/items/")
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.json()["results"]) >= 1

    def test_low_stock_filter(self, api_client, user, tenant):
        _auth(api_client)
        InventoryItem.objects.create(tenant=tenant, name="Low Item", category="supply", unit="piece",
                                     quantity_on_hand=3, reorder_point=10)
        InventoryItem.objects.create(tenant=tenant, name="OK Item", category="supply", unit="piece",
                                     quantity_on_hand=100, reorder_point=10)
        resp = api_client.get("/api/inventory/items/?low_stock=true")
        assert resp.status_code == status.HTTP_200_OK
        results = resp.json()["results"]
        assert len(results) == 1
        assert results[0]["name"] == "Low Item"

@pytest.mark.django_db
class TestStockMovements:
    def test_adjust_stock(self, api_client, user, tenant):
        _auth(api_client)
        item = InventoryItem.objects.create(tenant=tenant, name="Syringes", category="supply", unit="piece",
                                            quantity_on_hand=100)
        resp = api_client.post("/api/inventory/stock/adjust/", {
            "item_id": str(item.id), "quantity": "25",
            "movement_type": "adjustment", "reason": "Count correction",
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        item.refresh_from_db()
        assert item.quantity_on_hand == 125

    def test_waste_stock(self, api_client, user, tenant):
        _auth(api_client)
        item = InventoryItem.objects.create(tenant=tenant, name="Expired Med", category="medicine", unit="bottle",
                                            quantity_on_hand=50)
        resp = api_client.post("/api/inventory/stock/adjust/", {
            "item_id": str(item.id), "quantity": "10",
            "movement_type": "waste", "reason": "Expired",
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        item.refresh_from_db()
        assert item.quantity_on_hand == 40

@pytest.mark.django_db
class TestPurchaseOrders:
    def test_create_po(self, api_client, user, tenant):
        _auth(api_client)
        supplier = Supplier.objects.create(tenant=tenant, name="MedSupply Co")
        item = InventoryItem.objects.create(tenant=tenant, name="Bandages", category="supply", unit="box")

        resp = api_client.post("/api/inventory/orders/", {
            "supplier": str(supplier.id),
            "line_items": [{"item_id": str(item.id), "name": "Bandages", "quantity": 50, "unit_cost": "2.00"}],
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json()["po_number"].startswith("PO-")

    def test_receive_po(self, api_client, user, tenant):
        _auth(api_client)
        supplier = Supplier.objects.create(tenant=tenant, name="MedSupply Co")
        item = InventoryItem.objects.create(tenant=tenant, name="Bandages", category="supply", unit="box",
                                            quantity_on_hand=0)
        po = PurchaseOrder.objects.create(
            tenant=tenant, supplier=supplier, po_number="PO-2024-00001",
            line_items=[{"item_id": str(item.id), "name": "Bandages", "quantity": 50, "unit_cost": "2.00"}],
        )

        resp = api_client.post(f"/api/inventory/orders/{po.id}/receive/", {
            "item_receipts": [{"item_id": str(item.id), "quantity": "50"}],
        }, format="json")
        assert resp.status_code == status.HTTP_200_OK
        item.refresh_from_db()
        assert item.quantity_on_hand == 50
        po.refresh_from_db()
        assert po.status == PurchaseOrder.Status.RECEIVED

@pytest.mark.django_db
class TestBatches:
    def test_create_batch(self, api_client, user, tenant):
        _auth(api_client)
        item = InventoryItem.objects.create(tenant=tenant, name="Amoxicillin", category="medicine", unit="bottle",
                                            requires_batch_tracking=True)
        resp = api_client.post("/api/inventory/batches/", {
            "item": str(item.id), "lot_number": "LOT-2024-001",
            "quantity": "500", "expiration_date": "2026-12-31",
        }, format="json")
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.json()["lot_number"] == "LOT-2024-001"

    def test_expiring_batches(self, api_client, user, tenant):
        _auth(api_client)
        from django.utils import timezone
        import datetime
        item = InventoryItem.objects.create(tenant=tenant, name="Vaccine", category="medicine", unit="vial")
        Batch.objects.create(tenant=tenant, item=item, lot_number="LOT-EXPIRING", quantity=10,
                            expiration_date=timezone.now().date() + datetime.timedelta(days=30))
        resp = api_client.get("/api/inventory/batches/?expiring_soon=true")
        assert resp.status_code == status.HTTP_200_OK
