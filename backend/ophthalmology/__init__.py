"""Ophthalmology module — Sprint B6."""
from modules.registry import ModuleRegistry

def register():
    ModuleRegistry.register("ophthalmology",
        name="Ophthalmology", version="1.0.0",
        description="Eye exams, vision tests, lens prescriptions, retina imaging.",
        permissions=[
            ("ophth.read","View ophthalmology records"),
            ("ophth.write","Record eye exams"),
        ],
        appointment_types=[
            {"type":"eye_exam","label":"Eye Examination","color":"#0d9488","default_duration":30},
        ],
        patient_tabs=[
            {"label":"Eye Exams","icon":"eye","route":"eye-exams","permission":"ophth.read"},
        ],
        menu_items=[
            {"label":"Eye Exams","icon":"eye","path":"/ophth","permission":"ophth.read"},
        ],
        dashboard_widgets=[
            {"widget_type":"ophth_exams_today","title":"Eye Exams Today","width":1,"height":1},
        ],
        reports=[
            {"report_type":"ophth_prescription_volume","name":"Prescription Volume","category":"operational"},
        ],
    )
