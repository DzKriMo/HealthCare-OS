"""Veterinary module — Sprint B9."""
from modules.registry import ModuleRegistry
def register():
    ModuleRegistry.register("veterinary",
        name="Veterinary", version="1.0.0",
        description="Species/breed tracking, microchip registry, rabies certificates.",
        permissions=[("vet.read","View veterinary records"),("vet.write","Record veterinary findings")],
        appointment_types=[{"type":"vet_consult","label":"Veterinary Consultation","color":"#65a30d","default_duration":30}],
        patient_tabs=[{"label":"Veterinary","icon":"paw","route":"vet-records","permission":"vet.read"}],
    )
