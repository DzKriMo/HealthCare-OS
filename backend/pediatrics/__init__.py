"""Pediatrics module — Sprint B7."""
from modules.registry import ModuleRegistry

def register():
    ModuleRegistry.register("pediatrics",
        name="Pediatrics", version="1.0.0",
        description="Growth charts, vaccination schedules, developmental milestones.",
        permissions=[
            ("peds.read","View pediatric records"),
            ("peds.write","Record pediatric findings"),
        ],
        appointment_types=[
            {"type":"well_child","label":"Well-Child Visit","color":"#7c3aed","default_duration":30},
        ],
        patient_tabs=[
            {"label":"Growth Charts","icon":"barChart","route":"growth-charts","permission":"peds.read"},
        ],
        menu_items=[
            {"label":"Pediatrics","icon":"baby","path":"/peds","permission":"peds.read"},
        ],
        dashboard_widgets=[
            {"widget_type":"peds_vaccine_due","title":"Vaccinations Due","width":1,"height":1},
        ],
        reports=[
            {"report_type":"peds_growth","name":"Growth Percentile Report","category":"clinical"},
        ],
    )
