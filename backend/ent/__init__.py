"""ENT module — Sprint B8."""
from modules.registry import ModuleRegistry

def register():
    ModuleRegistry.register("ent",
        name="ENT", version="1.0.0",
        description="Audiology exams, endoscopy records, ENT care.",
        permissions=[("ent.read","View ENT records"),("ent.write","Record ENT findings")],
        appointment_types=[{"type":"ent_consult","label":"ENT Consultation","color":"#0891b2","default_duration":20}],
        patient_tabs=[{"label":"ENT","icon":"ear","route":"ent-records","permission":"ent.read"}],
        menu_items=[{"label":"ENT","icon":"ear","path":"/ent","permission":"ent.read"}],
        reports=[{"report_type":"ent_audiology","name":"Audiology Summary","category":"clinical"}],
    )
