"""Emergency/Urgent Care module — Sprint B9."""
from modules.registry import ModuleRegistry
def register():
    ModuleRegistry.register("emergency",
        name="Emergency & Urgent Care", version="1.0.0",
        description="Triage levels (ESI 1-5), chief complaint, disposition tracking.",
        permissions=[("er.read","View emergency records"),("er.write","Record emergency encounters")],
        appointment_types=[{"type":"er_visit","label":"Emergency Visit","color":"#dc2626","default_duration":60}],
        patient_tabs=[{"label":"Emergency","icon":"alert","route":"er-records","permission":"er.read"}],
    )
