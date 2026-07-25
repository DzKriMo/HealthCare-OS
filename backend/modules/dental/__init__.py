"""
Dental specialty module — Sprint 7.

The first specialty module, proving the module registry architecture.
Registers: permissions, patient tabs, menu items, dashboard widgets,
appointment types, billing codes, reports, and clinical templates.
"""
from modules.registry import ModuleRegistry


def register():
    """Register the dental module's capabilities into the platform registry."""
    ModuleRegistry.register(
        "dental",
        name="Dental",
        version="1.0.0",
        description="Odontogram, tooth charting, implants, crowns, treatment plans.",

        permissions=[
            ("modules.dental.access", "Access dental module features"),
            ("dental.chart.read", "View tooth charts"),
            ("dental.chart.write", "Edit tooth charts"),
            ("dental.treatment_plan.read", "View treatment plans"),
            ("dental.treatment_plan.write", "Create and edit treatment plans"),
            ("dental.procedures.read", "View dental procedures"),
            ("dental.procedures.perform", "Record dental procedures"),
        ],

        appointment_types=[
            {"type": "dental_consultation", "label": "Dental Consultation", "color": "#0284c7", "default_duration": 30},
            {"type": "dental_procedure", "label": "Dental Procedure", "color": "#7c3aed", "default_duration": 60},
            {"type": "dental_emergency", "label": "Dental Emergency", "color": "#dc2626", "default_duration": 30},
            {"type": "dental_hygiene", "label": "Hygiene / Cleaning", "color": "#16a34a", "default_duration": 45},
        ],

        patient_tabs=[
            {"label": "Dental Chart", "icon": "stethoscope", "route": "dental-chart", "permission": "dental.chart.read"},
            {"label": "Treatment Plans", "icon": "fileText", "route": "dental-plans", "permission": "dental.treatment_plan.read"},
            {"label": "Dental History", "icon": "barChart", "route": "dental-history", "permission": "dental.procedures.read"},
        ],

        menu_items=[
            {"label": "Tooth Chart", "icon": "stethoscope", "path": "/dental/chart", "permission": "dental.chart.read"},
            {"label": "Treatment Plans", "icon": "fileText", "path": "/dental/plans", "permission": "dental.treatment_plan.read"},
            {"label": "Dental Reports", "icon": "barChart", "path": "/dental/reports", "permission": "dental.chart.read"},
        ],

        dashboard_widgets=[
            {"widget_type": "dental_today_procedures", "title": "Today's Dental Procedures", "width": 2, "height": 1},
            {"widget_type": "dental_treatment_plans", "title": "Pending Treatment Plans", "width": 1, "height": 1},
            {"widget_type": "dental_follow_ups", "title": "Overdue Follow-Ups", "width": 1, "height": 1},
        ],

        billing_item_types=[
            {"category": "dental", "label": "Dental Procedure", "default_tax_rate": "8.50"},
        ],

        reports=[
            {"report_type": "dental_procedure_mix", "name": "Dental Procedure Mix", "category": "clinical"},
            {"report_type": "dental_treatment_completion", "name": "Treatment Plan Completion Rate", "category": "clinical"},
            {"report_type": "dental_tooth_status", "name": "Tooth Status Summary", "category": "clinical"},
        ],
    )
