"""Inventory module — Sprint B1."""
from modules.registry import ModuleRegistry


def register():
    ModuleRegistry.register(
        "inventory",
        name="Inventory",
        version="1.0.0",
        description="Medicines, supplies, equipment, stock tracking, purchase orders.",

        permissions=[
            ("inventory.read", "View inventory items and stock levels"),
            ("inventory.adjust_stock", "Adjust stock levels"),
            ("inventory.manage_suppliers", "Manage suppliers"),
            ("inventory.create_po", "Create purchase orders"),
            ("inventory.receive_po", "Receive purchase orders"),
            ("inventory.manage_batches", "Manage batch/lot tracking"),
        ],

        menu_items=[
            {"label": "Inventory", "icon": "package", "path": "/inventory", "permission": "inventory.read"},
            {"label": "Suppliers", "icon": "truck", "path": "/inventory/suppliers", "permission": "inventory.manage_suppliers"},
            {"label": "Purchase Orders", "icon": "clipboard", "path": "/inventory/orders", "permission": "inventory.create_po"},
        ],

        dashboard_widgets=[
            {"widget_type": "low_stock_alerts", "title": "Low Stock Items", "width": 2, "height": 1},
            {"widget_type": "expiring_batches", "title": "Expiring Soon", "width": 1, "height": 1},
            {"widget_type": "pending_pos", "title": "Pending Purchase Orders", "width": 1, "height": 1},
        ],

        billing_item_types=[
            {"category": "supplies", "label": "Medical Supplies", "default_tax_rate": "0.00"},
        ],

        reports=[
            {"report_type": "inventory_valuation", "name": "Inventory Valuation", "category": "operational"},
            {"report_type": "stock_movement", "name": "Stock Movement Report", "category": "operational"},
            {"report_type": "expiration_forecast", "name": "Expiration Forecast", "category": "operational"},
        ],
    )
