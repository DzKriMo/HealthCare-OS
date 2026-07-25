"""
Management command: seed base permissions and system roles.

Run: python manage.py seed_roles

Creates all base permissions (resource.action format) and the nine
standard system roles (Receptionist, Doctor, Nurse, Lab Technician,
Radiologist, Pharmacist, Manager, Admin, Super Admin).
"""
from django.core.management.base import BaseCommand
from identity.models import Permission, Role

# ── Base Permissions ──────────────────────────────────────────

BASE_PERMISSIONS = [
    # Patients
    ("patients.read", "View patient records", "patients", "read"),
    ("patients.write_demographics", "Edit patient demographics", "patients", "write_demographics"),
    ("patients.register", "Register new patients", "patients", "register"),
    ("patients.archive", "Archive patient records", "patients", "archive"),

    # Appointments
    ("appointments.read", "View appointments", "appointments", "read"),
    ("appointments.create", "Create appointments", "appointments", "create"),
    ("appointments.edit", "Edit appointments", "appointments", "edit"),
    ("appointments.cancel", "Cancel appointments", "appointments", "cancel"),
    ("appointments.manage_waitlist", "Manage waiting list", "appointments", "manage_waitlist"),

    # Medical Records / Encounters
    ("records.read", "View medical records", "records", "read"),
    ("records.write_assessment", "Write assessments and SOAP notes", "records", "write_assessment"),
    ("records.sign", "Sign clinical notes", "records", "sign"),
    ("records.prescribe", "Issue prescriptions", "records", "prescribe"),
    ("records.order_lab", "Order lab tests", "records", "order_lab"),
    ("records.order_imaging", "Order imaging studies", "records", "order_imaging"),

    # Billing
    ("billing.read", "View invoices and payments", "billing", "read"),
    ("billing.create_invoice", "Create invoices", "billing", "create_invoice"),
    ("billing.process_payment", "Process payments", "billing", "process_payment"),
    ("billing.refund", "Process refunds", "billing", "refund"),
    ("billing.view_finance", "View financial reports", "billing", "view_finance"),
    ("billing.manage_items", "Manage billing item catalog", "billing", "manage_items"),

    # Inventory
    ("inventory.read", "View inventory", "inventory", "read"),
    ("inventory.adjust_stock", "Adjust stock levels", "inventory", "adjust_stock"),
    ("inventory.manage_suppliers", "Manage suppliers", "inventory", "manage_suppliers"),
    ("inventory.create_po", "Create purchase orders", "inventory", "create_po"),

    # Documents
    ("documents.read", "View documents", "documents", "read"),
    ("documents.upload", "Upload documents", "documents", "upload"),
    ("documents.delete", "Delete documents", "documents", "delete"),

    # Notifications
    ("notifications.manage_templates", "Manage notification templates", "notifications", "manage_templates"),
    ("notifications.send", "Send notifications", "notifications", "send"),

    # Reports
    ("reports.view_operational", "View operational reports", "reports", "view_operational"),
    ("reports.view_finance", "View financial reports", "reports", "view_finance"),
    ("reports.view_clinical", "View clinical reports", "reports", "view_clinical"),
    ("reports.export", "Export reports", "reports", "export"),

    # Audit
    ("audit.read", "View audit logs", "audit", "read"),
    ("audit.export", "Export audit logs", "audit", "export"),

    # Module management
    ("modules.manage", "Enable/disable modules", "modules", "manage"),
    ("modules.dental.access", "Access dental module", "modules", "dental_access"),
    ("modules.laboratory.access", "Access laboratory module", "modules", "lab_access"),
    ("modules.imaging.access", "Access imaging module", "modules", "imaging_access"),
    ("modules.pharmacy.access", "Access pharmacy module", "modules", "pharmacy_access"),

    # Identity / Admin
    ("identity.manage_users", "Create and manage users", "identity", "manage_users"),
    ("identity.manage_roles", "Create and manage roles", "identity", "manage_roles"),
    ("identity.manage_tenant", "Manage tenant settings", "identity", "manage_tenant"),

    # Integrations
    ("integrations.manage", "Manage integrations and plugins", "integrations", "manage"),

    # Inventory
    ("inventory.read", "View inventory items", "inventory", "read"),
    ("inventory.adjust_stock", "Adjust stock levels", "inventory", "adjust_stock"),
    ("inventory.manage_suppliers", "Manage suppliers", "inventory", "manage_suppliers"),
    ("inventory.create_po", "Create purchase orders", "inventory", "create_po"),
    ("inventory.receive_po", "Receive purchase orders", "inventory", "receive_po"),
    ("inventory.manage_batches", "Manage batch/lot tracking", "inventory", "manage_batches"),

    # Pharmacy
    ("pharmacy.prescribe", "Write prescriptions", "pharmacy", "prescribe"),
    ("pharmacy.dispense", "Dispense medications", "pharmacy", "dispense"),
    ("pharmacy.controlled", "Access controlled substance features", "pharmacy", "controlled"),
    ("pharmacy.read", "View pharmacy records", "pharmacy", "read"),

    # Clinical
    ("clinical.read", "View clinical records", "clinical", "read"),
    ("clinical.write", "Write encounter notes", "clinical", "write"),
    ("clinical.diagnose", "Record diagnoses", "clinical", "diagnose"),
    ("clinical.refer", "Create referrals", "clinical", "refer"),

    # Imaging
    ("imaging.read", "View imaging studies", "imaging", "read"),
    ("imaging.upload", "Upload imaging studies", "imaging", "upload"),
    ("imaging.report", "Write radiology reports", "imaging", "report"),
    ("imaging.sign", "Sign radiology reports", "imaging", "sign"),

    # Dermatology
    ("derm.read", "View dermatology records", "derm", "read"),
    ("derm.write", "Record dermatology findings", "derm", "write"),

    # Ophthalmology
    ("ophth.read", "View ophthalmology records", "ophth", "read"),
    ("ophth.write", "Record eye exams", "ophth", "write"),

    # Cardiology
    ("cardio.read", "View cardiology records", "cardio", "read"),
    ("cardio.write", "Record cardiology findings", "cardio", "write"),

    # Gynecology
    ("gyn.read", "View gynecology records", "gyn", "read"),
    ("gyn.write", "Record gynecology findings", "gyn", "write"),

    # Orthopedics
    ("ortho.read", "View orthopedics records", "ortho", "read"),
    ("ortho.write", "Record orthopedics findings", "ortho", "write"),

    # Physiotherapy
    ("physio.read", "View physiotherapy records", "physio", "read"),
    ("physio.write", "Record physiotherapy notes", "physio", "write"),

    # Dialysis
    ("dialysis.read", "View dialysis records", "dialysis", "read"),
    ("dialysis.write", "Record dialysis sessions", "dialysis", "write"),

    # Oncology
    ("onc.read", "View oncology records", "onc", "read"),
    ("onc.write", "Record oncology findings", "onc", "write"),

    # Emergency
    ("er.read", "View emergency records", "er", "read"),
    ("er.write", "Record emergency encounters", "er", "write"),

    # Veterinary
    ("vet.read", "View veterinary records", "vet", "read"),
    ("vet.write", "Record veterinary findings", "vet", "write"),

    # ENT
    ("ent.read", "View ENT records", "ent", "read"),
    ("ent.write", "Record ENT findings", "ent", "write"),

    # Pediatrics
    ("peds.read", "View pediatric records", "peds", "read"),
    ("peds.write", "Record pediatric findings", "peds", "write"),

    # Laboratory
    ("lab.read", "View lab orders and results", "lab", "read"),
    ("lab.order", "Order lab tests", "lab", "order"),
    ("lab.collect", "Collect and accession specimens", "lab", "collect"),
    ("lab.result", "Enter and edit lab results", "lab", "result"),
    ("lab.approve", "Approve and sign lab results", "lab", "approve"),

    # Sync
    ("sync.access", "Access offline sync features", "sync", "access"),
]

# ── Base Roles ────────────────────────────────────────────────

BASE_ROLES = {
    "Receptionist": {
        "description": "Front-desk: appointments, patient registration, payments, documents.",
        "permissions": [
            "patients.read", "patients.write_demographics", "patients.register",
            "appointments.read", "appointments.create", "appointments.edit", "appointments.cancel",
            "billing.read", "billing.create_invoice", "billing.process_payment",
            "documents.read", "documents.upload",
        ],
    },
    "Doctor": {
        "description": "Clinical: encounters, assessments, prescriptions, lab orders.",
        "permissions": [
            "patients.read", "patients.write_demographics",
            "appointments.read",
            "records.read", "records.write_assessment", "records.sign",
            "records.prescribe", "records.order_lab", "records.order_imaging",
            "documents.read", "documents.upload",
            "reports.view_clinical",
        ],
    },
    "Nurse": {
        "description": "Clinical support: vitals, triage, care workflows.",
        "permissions": [
            "patients.read",
            "appointments.read",
            "records.read", "records.write_assessment",
            "records.order_lab",
            "documents.read", "documents.upload",
        ],
    },
    "Lab Technician": {
        "description": "Laboratory: sample management, result entry.",
        "permissions": [
            "patients.read",
            "records.read", "records.order_lab",
            "inventory.read", "inventory.adjust_stock",
            "documents.read", "documents.upload",
            "modules.laboratory.access",
        ],
    },
    "Radiologist": {
        "description": "Radiology: image review, annotations, reports.",
        "permissions": [
            "patients.read",
            "records.read", "records.order_imaging",
            "records.write_assessment", "records.sign",
            "documents.read", "documents.upload",
            "modules.imaging.access",
        ],
    },
    "Pharmacist": {
        "description": "Pharmacy: prescriptions, dispensing, inventory.",
        "permissions": [
            "patients.read",
            "records.read", "records.prescribe",
            "inventory.read", "inventory.adjust_stock", "inventory.manage_suppliers",
            "billing.read", "billing.process_payment",
            "modules.pharmacy.access",
        ],
    },
    "Manager": {
        "description": "Operations: reports, finance, staff oversight.",
        "permissions": [
            "patients.read",
            "appointments.read", "appointments.manage_waitlist",
            "records.read",
            "billing.read", "billing.create_invoice", "billing.process_payment",
            "billing.refund", "billing.view_finance", "billing.manage_items",
            "inventory.read", "inventory.adjust_stock", "inventory.manage_suppliers", "inventory.create_po",
            "documents.read",
            "notifications.manage_templates", "notifications.send",
            "reports.view_operational", "reports.view_finance", "reports.view_clinical", "reports.export",
            "audit.read",
            "modules.manage",
        ],
    },
    "Admin": {
        "description": "Tenant administration: users, roles, settings, all modules.",
        "permissions": [
            "patients.read", "patients.write_demographics", "patients.register", "patients.archive",
            "appointments.read", "appointments.create", "appointments.edit",
            "appointments.cancel", "appointments.manage_waitlist",
            "records.read", "records.write_assessment", "records.sign",
            "records.prescribe", "records.order_lab", "records.order_imaging",
            "billing.read", "billing.create_invoice", "billing.process_payment",
            "billing.refund", "billing.view_finance", "billing.manage_items",
            "inventory.read", "inventory.adjust_stock", "inventory.manage_suppliers", "inventory.create_po",
            "documents.read", "documents.upload", "documents.delete",
            "notifications.manage_templates", "notifications.send",
            "reports.view_operational", "reports.view_finance", "reports.view_clinical", "reports.export",
            "audit.read", "audit.export",
            "modules.manage", "modules.dental.access", "modules.laboratory.access",
            "modules.imaging.access", "modules.pharmacy.access",
            "identity.manage_users", "identity.manage_roles", "identity.manage_tenant",
            "integrations.manage",
        ],
    },
    "Super Admin": {
        "description": "Cross-tenant platform administration.",
        "permissions": [p[0] for p in BASE_PERMISSIONS],  # All permissions
    },
}


class Command(BaseCommand):
    help = "Seed base permissions and system roles."

    def handle(self, *args, **options):
        self._seed_permissions()
        self._seed_roles()

    def _seed_permissions(self):
        created = 0
        for codename, description, resource, action in BASE_PERMISSIONS:
            _, created_flag = Permission.objects.get_or_create(
                codename=codename,
                defaults={
                    "description": description,
                    "resource": resource,
                    "action": action,
                },
            )
            if created_flag:
                created += 1
        self.stdout.write(
            self.style.SUCCESS(f"Permissions: {created} created, "
                               f"{len(BASE_PERMISSIONS) - created} already exist.")
        )

    def _seed_roles(self):
        created = 0
        for role_name, config in BASE_ROLES.items():
            role, created_flag = Role.objects.get_or_create(
                name=role_name,
                is_system_role=True,
                tenant=None,
                defaults={"description": config["description"]},
            )
            if created_flag:
                created += 1
            # Sync permissions
            perms = Permission.objects.filter(codename__in=config["permissions"])
            role.permissions.set(perms)
            role.save()

        self.stdout.write(
            self.style.SUCCESS(f"Roles: {created} created, "
                               f"{len(BASE_ROLES) - created} already exist.")
        )
