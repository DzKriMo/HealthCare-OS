"""Oncology module — Sprint B9."""
from modules.registry import ModuleRegistry
def register():
    ModuleRegistry.register("oncology",
        name="Oncology", version="1.0.0",
        description="Cancer staging (TNM), chemotherapy protocols, tumor markers, radiation tracking.",
        permissions=[("onc.read","View oncology records"),("onc.write","Record oncology findings")],
        appointment_types=[{"type":"onc_consult","label":"Oncology Consultation","color":"#a855f7","default_duration":45}],
        patient_tabs=[{"label":"Oncology","icon":"shield","route":"onc-records","permission":"onc.read"}],
    )
