"""Dialysis module — Sprint B9."""
from modules.registry import ModuleRegistry
def register():
    ModuleRegistry.register("dialysis",
        name="Dialysis", version="1.0.0",
        description="Treatment sessions, pre/post vitals, fluid removal, access site monitoring.",
        permissions=[("dialysis.read","View dialysis records"),("dialysis.write","Record dialysis sessions")],
        appointment_types=[{"type":"dialysis_session","label":"Dialysis Session","color":"#06b6d4","default_duration":240}],
        patient_tabs=[{"label":"Dialysis","icon":"droplet","route":"dialysis-records","permission":"dialysis.read"}],
    )
