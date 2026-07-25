"""Cardiology module — Sprint B7."""
from modules.registry import ModuleRegistry

def register():
    ModuleRegistry.register("cardiology",
        name="Cardiology", version="1.0.0",
        description="ECG, echo reports, BP history, cardiovascular risk scoring.",
        permissions=[
            ("cardio.read","View cardiology records"),
            ("cardio.write","Record cardiology findings"),
        ],
        appointment_types=[
            {"type":"cardio_consult","label":"Cardiology Consultation","color":"#dc2626","default_duration":30},
        ],
        patient_tabs=[
            {"label":"Cardiology","icon":"heart","route":"cardio-records","permission":"cardio.read"},
        ],
        menu_items=[
            {"label":"Cardiology","icon":"heart","path":"/cardio","permission":"cardio.read"},
        ],
        dashboard_widgets=[
            {"widget_type":"cardio_abnormal","title":"Abnormal ECGs","width":1,"height":1},
        ],
        reports=[
            {"report_type":"cardio_risk_distribution","name":"CV Risk Distribution","category":"clinical"},
        ],
    )
