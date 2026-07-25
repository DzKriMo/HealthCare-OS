"""Dermatology module — Sprint B6."""
from modules.registry import ModuleRegistry

def register():
    ModuleRegistry.register("dermatology",
        name="Dermatology", version="1.0.0",
        description="Body mapping, lesion tracking, photo timeline, procedure history.",
        permissions=[
            ("derm.read","View dermatology records"),
            ("derm.write","Record dermatology findings"),
        ],
        appointment_types=[
            {"type":"derm_consult","label":"Dermatology Consultation","color":"#a855f7","default_duration":20},
        ],
        patient_tabs=[
            {"label":"Dermatology","icon":"camera","route":"derm-chart","permission":"derm.read"},
        ],
        menu_items=[
            {"label":"Body Map","icon":"camera","path":"/derm","permission":"derm.read"},
        ],
        dashboard_widgets=[
            {"widget_type":"derm_pending","title":"Pending Reviews","width":1,"height":1},
        ],
        reports=[
            {"report_type":"derm_procedure_mix","name":"Procedure Mix","category":"clinical"},
        ],
    )
