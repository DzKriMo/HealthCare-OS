"""
Management command: create a fully populated demo environment.

Run: python manage.py seed_demo

Creates:
    - Demo tenant with branding and settings
    - All system roles and permissions (via seed_roles)
    - Demo users: admin, doctor, receptionist
    - Billing items catalog (consultation, cleaning, filling, x-ray, etc.)
    - Sample patients with medical history, allergies, insurance, contacts
    - Today's appointments for demo patients
    - Sample invoices with payments
"""
import datetime
import decimal
import random
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.contrib.auth import get_user_model
from django.utils import timezone

from tenancy.models import Tenant, TenantSettings
from identity.models import Role
from patients.models import Patient, MedicalHistory, Allergy, InsurancePolicy, EmergencyContact
from scheduling.models import Appointment, Room, PractitionerSchedule
from billing.models import BillingItem, Invoice, Payment

User = get_user_model()

SAMPLE_PATIENTS = [
    {
        "first_name": "Emily", "last_name": "Johnson",
        "date_of_birth": "1990-03-15", "gender": "female", "blood_type": "A+",
        "phone_primary": "+1 (555) 123-4567", "email": "emily.j@email.com",
        "city": "Austin", "marital_status": "married",
        "allergies": [{"substance": "Penicillin", "reaction": "Rash", "severity": "moderate"}],
    },
    {
        "first_name": "Michael", "last_name": "Chen",
        "date_of_birth": "1985-07-22", "gender": "male", "blood_type": "O+",
        "phone_primary": "+1 (555) 234-5678", "email": "m.chen@email.com",
        "city": "Austin", "marital_status": "single",
        "allergies": [{"substance": "Sulfa", "reaction": "Nausea", "severity": "mild"}],
    },
    {
        "first_name": "Sophia", "last_name": "Martinez",
        "date_of_birth": "1978-11-02", "gender": "female", "blood_type": "B+",
        "phone_primary": "+1 (555) 345-6789", "email": "sophia.m@email.com",
        "city": "Round Rock", "marital_status": "married",
        "allergies": [
            {"substance": "Latex", "reaction": "Contact dermatitis", "severity": "mild"},
            {"substance": "Codeine", "reaction": "Drowsiness", "severity": "moderate"},
        ],
    },
    {
        "first_name": "James", "last_name": "Williams",
        "date_of_birth": "1965-01-10", "gender": "male", "blood_type": "A-",
        "phone_primary": "+1 (555) 456-7890", "email": "jwilliams@email.com",
        "city": "Cedar Park", "marital_status": "widowed",
        "allergies": [],
    },
    {
        "first_name": "Olivia", "last_name": "Brown",
        "date_of_birth": "2000-09-05", "gender": "female", "blood_type": "AB+",
        "phone_primary": "+1 (555) 567-8901", "email": "olivia.b@email.com",
        "city": "Austin", "marital_status": "single",
        "allergies": [{"substance": "Peanuts", "reaction": "Anaphylaxis", "severity": "severe"}],
    },
    {
        "first_name": "Robert", "last_name": "Davis",
        "date_of_birth": "1995-12-18", "gender": "male", "blood_type": "O-",
        "phone_primary": "+1 (555) 678-9012", "email": "rob.davis@email.com",
        "city": "Pflugerville", "marital_status": "single",
        "allergies": [],
    },
]

BILLING_ITEMS = [
    {"name": "General Consultation", "category": "consultation", "price": "150.00"},
    {"name": "Follow-up Visit", "category": "consultation", "price": "75.00"},
    {"name": "Teeth Cleaning (Adult)", "category": "procedure", "price": "200.00"},
    {"name": "Composite Filling (1 surface)", "category": "procedure", "price": "250.00"},
    {"name": "Composite Filling (2 surfaces)", "category": "procedure", "price": "350.00"},
    {"name": "Root Canal (Anterior)", "category": "procedure", "price": "900.00"},
    {"name": "Root Canal (Molar)", "category": "procedure", "price": "1400.00"},
    {"name": "Crown (Porcelain)", "category": "procedure", "price": "1200.00"},
    {"name": "X-Ray (Full Mouth)", "category": "imaging", "price": "150.00"},
    {"name": "X-Ray (Bitewing)", "category": "imaging", "price": "50.00"},
    {"name": "Tooth Extraction (Simple)", "category": "procedure", "price": "200.00"},
    {"name": "Tooth Extraction (Surgical)", "category": "procedure", "price": "400.00"},
    {"name": "Teeth Whitening", "category": "procedure", "price": "500.00"},
    {"name": "Fluoride Treatment", "category": "procedure", "price": "35.00"},
    {"name": "CBC Blood Test", "category": "lab", "price": "85.00"},
    {"name": "COVID-19 Rapid Test", "category": "lab", "price": "25.00"},
]


class Command(BaseCommand):
    help = "Seed full demo environment: tenant, roles, users, patients, appointments, billing."

    def handle(self, *args, **options):
        call_command("seed_roles")

        tenant = self._create_tenant()
        admin, doctor, receptionist = self._create_users(tenant)
        items = self._create_billing_items(tenant)
        rooms = self._create_rooms(tenant)
        self._create_practitioner_schedule(doctor, tenant)
        patients = self._create_patients(tenant, admin)
        self._create_appointments(patients, doctor, rooms, tenant)
        self._create_invoices(patients, items, admin, tenant)

        self.stdout.write(self.style.SUCCESS("\n✅ Demo environment ready!"))
        self.stdout.write(f"   Tenant:   {tenant.slug}")
        self.stdout.write(f"   Admin:    admin@smileclinic.com / demopass123")
        self.stdout.write(f"   Doctor:   doctor@smileclinic.com / demopass123")
        self.stdout.write(f"   Reception: reception@smileclinic.com / demopass123")
        self.stdout.write(f"   Patients: {len(patients)} created")
        self.stdout.write(f"   Items:    {len(items)} billing items")
        self.stdout.write(f"   Rooms:    {len(rooms)} rooms")

    def _create_tenant(self):
        tenant, created = Tenant.objects.get_or_create(
            slug="smile-dental",
            defaults={
                "name": "Smile Dental Clinic",
                "branding": {
                    "primary_color": "#0369a1",
                    "secondary_color": "#f0f9ff",
                    "clinic_name": "Smile Dental Clinic",
                    "language": "en",
                    "currency": "USD",
                },
                "settings": {
                    "timezone": "America/Chicago",
                    "date_format": "MM/DD/YYYY",
                    "notification_channels": {"email": True, "sms": False, "whatsapp": False, "push": False},
                },
                "enabled_modules": ["dental", "billing", "documents", "notifications", "clinical", "patients", "scheduling"],
                "subscription_status": "trial",
            },
        )
        if created:
            TenantSettings.objects.create(tenant=tenant)
            self.stdout.write(f"Created tenant: {tenant.name}")
        return tenant

    def _create_users(self, tenant):
        roles = {
            "admin": Role.objects.get(name="Admin", is_system_role=True),
            "doctor": Role.objects.get(name="Doctor", is_system_role=True),
            "receptionist": Role.objects.get(name="Receptionist", is_system_role=True),
        }
        users_data = [
            {"email": "admin@smileclinic.com", "first_name": "Sarah", "last_name": "Admin", "role": roles["admin"], "password": "demopass123"},
            {"email": "doctor@smileclinic.com", "first_name": "James", "last_name": "Wilson", "role": roles["doctor"], "password": "demopass123", "license_number": "DDS-2024-00123", "specialty": "General Dentistry"},
            {"email": "reception@smileclinic.com", "first_name": "Maria", "last_name": "Garcia", "role": roles["receptionist"], "password": "demopass123"},
        ]
        created_users = []
        for data in users_data:
            role = data.pop("role")
            password = data.pop("password")
            user, _ = User.objects.get_or_create(email=data["email"], defaults={"tenant": tenant, "role": role, **data})
            if _:
                user.set_password(password)
                user.save()
            created_users.append(user)
        return created_users

    def _create_billing_items(self, tenant):
        items = []
        for item_data in BILLING_ITEMS:
            item, created = BillingItem.objects.get_or_create(
                tenant=tenant, name=item_data["name"],
                defaults={"category": item_data["category"], "price": item_data["price"]},
            )
            items.append(item)
        self.stdout.write(f"   Billing items: {len(items)}")
        return items

    def _create_rooms(self, tenant):
        rooms = []
        for name, color in [("Treatment Room 1", "#0369a1"), ("Treatment Room 2", "#7c3aed"), ("Surgery Suite", "#dc2626"), ("Consultation", "#059669")]:
            room, _ = Room.objects.get_or_create(tenant=tenant, name=name, defaults={"color": color})
            rooms.append(room)
        return rooms

    def _create_practitioner_schedule(self, doctor, tenant):
        for day in range(5):
            PractitionerSchedule.objects.get_or_create(
                tenant=tenant, practitioner=doctor, day_of_week=day,
                defaults={"start_time": datetime.time(8, 0), "end_time": datetime.time(17, 0), "slot_duration_minutes": 30, "is_active": True},
            )

    def _create_patients(self, tenant, admin):
        patients = []
        today = timezone.now().date()
        for i, data in enumerate(SAMPLE_PATIENTS):
            allergies = data.pop("allergies", [])
            patient, created = Patient.objects.get_or_create(
                tenant=tenant, first_name=data["first_name"], last_name=data["last_name"],
                defaults={
                    "date_of_birth": data["date_of_birth"],
                    "gender": data["gender"],
                    "blood_type": data["blood_type"],
                    "phone_primary": data["phone_primary"],
                    "email": data["email"],
                    "city": data.get("city", ""),
                    "marital_status": data.get("marital_status", "unknown"),
                    "display_id": f"PAT-{today.year}-{i + 1:04d}",
                    "created_by": admin,
                },
            )
            if not created:
                patients.append(patient)
                continue

            for allergy in allergies:
                Allergy.objects.create(tenant=tenant, patient=patient, recorded_by=admin, **allergy)

            EmergencyContact.objects.create(
                tenant=tenant, patient=patient, name="Jane Doe",
                relationship="spouse" if data.get("marital_status") == "married" else "parent",
                phone_primary="+1 (555) 999-0000",
            )

            InsurancePolicy.objects.create(
                tenant=tenant, patient=patient, provider="Blue Cross Blue Shield",
                policy_number=f"BCBS-{random.randint(100000, 999999)}",
                coverage_type="PPO", effective_date=today - datetime.timedelta(days=365),
                expiration_date=today + datetime.timedelta(days=365),
                is_verified=True,
            )

            patients.append(patient)
            self.stdout.write(f"   Patient: {patient.full_name}")

        return patients

    def _create_appointments(self, patients, doctor, rooms, tenant):
        today = timezone.now().date()
        statuses = ["scheduled", "confirmed", "arrived", "completed"]
        start_hours = [8, 9, 10, 11, 13, 14, 15, 16]

        for i, patient in enumerate(patients[:4]):
            hour = start_hours[i % len(start_hours)]
            start = timezone.make_aware(datetime.datetime(today.year, today.month, today.day, hour, 0))
            status = statuses[i % len(statuses)]
            Appointment.objects.get_or_create(
                tenant=tenant, patient=patient, practitioner=doctor,
                start_time=start,
                defaults={
                    "end_time": start + datetime.timedelta(minutes=30),
                    "type": "consultation",
                    "status": status,
                    "room": rooms[i % len(rooms)],
                },
            )

    def _create_invoices(self, patients, items, admin, tenant):
        today = timezone.now().date()
        statuses = ["paid", "paid", "partially_paid", "issued", "overdue"]

        for i, patient in enumerate(patients[:5]):
            selected = random.sample(items, random.randint(1, 3))
            line_items = []
            subtotal = decimal.Decimal("0")
            for item in selected:
                qty = random.randint(1, 2)
                line = {
                    "billing_item_id": str(item.id),
                    "description": item.name,
                    "quantity": qty,
                    "unit_price": str(item.price),
                    "tax_rate": "8.25",
                }
                line_items.append(line)
                subtotal += item.price * qty

            tax_total = subtotal * decimal.Decimal("0.0825")
            grand_total = subtotal + tax_total
            inv_number = f"INV-{today.year}-{i + 1:04d}"
            status = statuses[i]

            inv, created = Invoice.objects.get_or_create(
                tenant=tenant, invoice_number=inv_number,
                defaults={
                    "patient": patient,
                    "status": status,
                    "line_items": line_items,
                    "subtotal": subtotal,
                    "tax_total": tax_total,
                    "grand_total": grand_total,
                    "amount_paid": grand_total if status == "paid" else (grand_total / 2 if status == "partially_paid" else decimal.Decimal("0")),
                    "balance_due": decimal.Decimal("0") if status == "paid" else (grand_total / 2 if status == "partially_paid" else grand_total),
                    "issued_date": today,
                    "due_date": today + datetime.timedelta(days=30),
                    "created_by": admin,
                },
            )

            if created and status == "paid":
                Payment.objects.create(
                    tenant=tenant, invoice=inv, patient=patient,
                    amount=grand_total, method="card",
                    reference=f"TXN-{random.randint(100000, 999999)}",
                    processed_by=admin,
                )
