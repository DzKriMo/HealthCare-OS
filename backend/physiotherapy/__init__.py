"""Physiotherapy module — Sprint B9."""
from modules.registry import ModuleRegistry
def register():
    ModuleRegistry.register("physiotherapy",
        name="Physiotherapy", version="1.0.0",
        description="Treatment plans, exercise library, session notes, progress tracking.",
        permissions=[("physio.read","View physiotherapy records"),("physio.write","Record physiotherapy notes")],
        appointment_types=[{"type":"physio_session","label":"Physiotherapy Session","color":"#84cc16","default_duration":45}],
        patient_tabs=[{"label":"Physiotherapy","icon":"activity","route":"physio-records","permission":"physio.read"}],
        menu_items=[{"label":"Physiotherapy","icon":"activity","path":"/physio","permission":"physio.read"}],
    )
