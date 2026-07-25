"""Laboratory module — Sprint B3."""
from modules.registry import ModuleRegistry


def register():
    ModuleRegistry.register(
        "laboratory",
        name="Laboratory",
        version="1.0.0",
        description="Test catalog, specimen tracking, result entry, approval workflows.",

        permissions=[
            ("modules.laboratory.access", "Access laboratory module"),
            ("lab.read", "View lab orders and results"),
            ("lab.order", "Order lab tests"),
            ("lab.collect", "Collect and accession specimens"),
            ("lab.result", "Enter and edit lab results"),
            ("lab.approve", "Approve and sign lab results"),
        ],

        appointment_types=[
            {"type": "lab_collection", "label": "Lab Collection", "color": "#7c3aed", "default_duration": 15},
        ],

        patient_tabs=[
            {"label": "Lab Results", "icon": "barChart", "route": "lab-results", "permission": "lab.read"},
            {"label": "Lab Orders", "icon": "fileText", "route": "lab-orders", "permission": "lab.read"},
        ],

        menu_items=[
            {"label": "Lab Orders", "icon": "fileText", "path": "/lab/orders", "permission": "lab.read"},
            {"label": "Specimens", "icon": "package", "path": "/lab/specimens", "permission": "lab.collect"},
            {"label": "Result Entry", "icon": "barChart", "path": "/lab/results", "permission": "lab.result"},
        ],

        dashboard_widgets=[
            {"widget_type": "lab_pending_results", "title": "Pending Results", "width": 1, "height": 1},
            {"widget_type": "lab_critical_flags", "title": "Critical Results", "width": 1, "height": 1},
            {"widget_type": "lab_turnaround", "title": "Avg Turnaround", "width": 1, "height": 1},
        ],

        reports=[
            {"report_type": "lab_turnaround_time", "name": "Turnaround Time Report", "category": "operational"},
            {"report_type": "lab_test_volume", "name": "Test Volume Report", "category": "operational"},
            {"report_type": "lab_abnormal_rate", "name": "Abnormal Result Rate", "category": "clinical"},
        ],
    )
