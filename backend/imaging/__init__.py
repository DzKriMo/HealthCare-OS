"""Imaging/Radiology module — Sprint B4."""
from modules.registry import ModuleRegistry

def register():
    ModuleRegistry.register("imaging",
        name="Imaging & Radiology", version="1.0.0",
        description="DICOM study management, image storage, radiologist reporting.",
        permissions=[
            ("modules.imaging.access","Access imaging module"),
            ("imaging.read","View imaging studies and reports"),
            ("imaging.upload","Upload imaging studies"),
            ("imaging.report","Write radiology reports"),
            ("imaging.sign","Sign and finalize reports"),
        ],
        appointment_types=[
            {"type":"imaging","label":"Imaging Appointment","color":"#0891b2","default_duration":30},
        ],
        patient_tabs=[
            {"label":"Imaging","icon":"barChart","route":"imaging-studies","permission":"imaging.read"},
        ],
        menu_items=[
            {"label":"Imaging Studies","icon":"barChart","path":"/imaging","permission":"imaging.read"},
            {"label":"Reports","icon":"fileText","path":"/imaging/reports","permission":"imaging.report"},
        ],
        dashboard_widgets=[
            {"widget_type":"imaging_pending","title":"Pending Reports","width":1,"height":1},
            {"widget_type":"imaging_volume","title":"Today's Studies","width":1,"height":1},
        ],
        reports=[
            {"report_type":"imaging_volume","name":"Imaging Volume by Modality","category":"operational"},
            {"report_type":"imaging_turnaround","name":"Report Turnaround Time","category":"operational"},
        ],
    )
