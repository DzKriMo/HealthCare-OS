"""Pharmacy module — Sprint B2."""
from modules.registry import ModuleRegistry


def register():
    ModuleRegistry.register(
        "pharmacy",
        name="Pharmacy",
        version="1.0.0",
        description="Prescriptions, dispensing, controlled substances, retail POS.",

        permissions=[
            ("modules.pharmacy.access", "Access pharmacy module"),
            ("pharmacy.prescribe", "Write prescriptions"),
            ("pharmacy.dispense", "Dispense medications"),
            ("pharmacy.controlled", "Access controlled substance features"),
            ("pharmacy.read", "View prescriptions and dispense records"),
        ],

        appointment_types=[
            {"type": "pharmacy_consult", "label": "Pharmacist Consultation", "color": "#059669", "default_duration": 15},
        ],

        patient_tabs=[
            {"label": "Prescriptions", "icon": "fileText", "route": "pharmacy-prescriptions", "permission": "pharmacy.read"},
            {"label": "Dispense History", "icon": "barChart", "route": "pharmacy-history", "permission": "pharmacy.read"},
        ],

        menu_items=[
            {"label": "Prescriptions", "icon": "fileText", "path": "/pharmacy", "permission": "pharmacy.read"},
            {"label": "Dispense", "icon": "package", "path": "/pharmacy/dispense", "permission": "pharmacy.dispense"},
            {"label": "Controlled Substances", "icon": "shield", "path": "/pharmacy/controlled", "permission": "pharmacy.controlled"},
        ],

        dashboard_widgets=[
            {"widget_type": "pharmacy_pending", "title": "Pending Prescriptions", "width": 1, "height": 1},
            {"widget_type": "pharmacy_dispensed_today", "title": "Dispensed Today", "width": 1, "height": 1},
            {"widget_type": "pharmacy_low_stock", "title": "Low Stock Meds", "width": 1, "height": 1},
        ],

        billing_item_types=[
            {"category": "pharmacy", "label": "Pharmacy Dispensing", "default_tax_rate": "0.00"},
        ],

        reports=[
            {"report_type": "pharmacy_dispensing_volume", "name": "Dispensing Volume", "category": "operational"},
            {"report_type": "pharmacy_controlled_audit", "name": "Controlled Substance Audit", "category": "clinical"},
            {"report_type": "pharmacy_refill_analysis", "name": "Refill Analysis", "category": "operational"},
        ],
    )
