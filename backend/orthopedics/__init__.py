"""Orthopedics module — Sprint B8."""
from modules.registry import ModuleRegistry

def register():
    ModuleRegistry.register("orthopedics",
        name="Orthopedics", version="1.0.0",
        description="Joint assessments, fracture records, physiotherapy plans.",
        permissions=[("ortho.read","View orthopedics records"),("ortho.write","Record orthopedics findings")],
        appointment_types=[{"type":"ortho_consult","label":"Orthopedic Consultation","color":"#f97316","default_duration":30}],
        patient_tabs=[{"label":"Orthopedics","icon":"activity","route":"ortho-records","permission":"ortho.read"}],
        menu_items=[{"label":"Orthopedics","icon":"activity","path":"/ortho","permission":"ortho.read"}],
        reports=[{"report_type":"ortho_fracture","name":"Fracture Incidence","category":"clinical"}],
    )
