"""Clinical/General Medicine module — Sprint B5."""
from modules.registry import ModuleRegistry

def register():
    ModuleRegistry.register("general_medicine",
        name="General Medicine", version="1.0.0",
        description="SOAP encounters, diagnoses, referrals, vitals, vaccinations, family/social history.",
        permissions=[
            ("clinical.read","View clinical records"),
            ("clinical.write","Write encounter notes"),
            ("clinical.diagnose","Record diagnoses"),
            ("clinical.refer","Create referrals"),
        ],
        appointment_types=[
            {"type":"gp_consult","label":"GP Consultation","color":"#2563eb","default_duration":20},
            {"type":"follow_up","label":"Follow-Up","color":"#059669","default_duration":15},
        ],
        patient_tabs=[
            {"label":"Encounters","icon":"fileText","route":"encounters","permission":"clinical.read"},
            {"label":"Vitals","icon":"barChart","route":"vitals","permission":"clinical.read"},
            {"label":"Diagnoses","icon":"shield","route":"diagnoses","permission":"clinical.read"},
        ],
        menu_items=[
            {"label":"Encounters","icon":"fileText","path":"/clinical","permission":"clinical.read"},
            {"label":"Referrals","icon":"share","path":"/clinical/referrals","permission":"clinical.refer"},
        ],
        dashboard_widgets=[
            {"widget_type":"encounters_today","title":"Today's Encounters","width":1,"height":1},
            {"widget_type":"common_diagnoses","title":"Top Diagnoses","width":2,"height":1},
        ],
        reports=[
            {"report_type":"diagnosis_distribution","name":"Diagnosis Distribution","category":"clinical"},
            {"report_type":"referral_patterns","name":"Referral Patterns","category":"clinical"},
        ],
    )
