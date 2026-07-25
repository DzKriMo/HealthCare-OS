"""Gynecology module — Sprint B8."""
from modules.registry import ModuleRegistry

def register():
    ModuleRegistry.register("gynecology",
        name="Gynecology", version="1.0.0",
        description="OB history, Pap smears, antenatal visits, gynecological care.",
        permissions=[
            ("gyn.read","View gynecology records"),
            ("gyn.write","Record gynecology findings"),
        ],
        appointment_types=[
            {"type":"gyn_consult","label":"Gynecology Consultation","color":"#ec4899","default_duration":20},
        ],
        patient_tabs=[
            {"label":"Gynecology","icon":"heart","route":"gyn-records","permission":"gyn.read"},
        ],
        menu_items=[{"label":"Gynecology","icon":"heart","path":"/gyn","permission":"gyn.read"}],
        reports=[{"report_type":"gyn_pap_coverage","name":"Pap Smear Coverage","category":"clinical"}],
    )
