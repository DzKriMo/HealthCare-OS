"""Veterinary models."""
import uuid; from django.db import models; from django.utils import timezone
from tenancy.models import Tenant; from tenancy.managers import TenantScopedManager; from patients.models import Patient

class AnimalRecord(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="animal_records")
    patient = models.OneToOneField(Patient, on_delete=models.CASCADE, related_name="animal_record")
    species = models.CharField(max_length=50, choices=[("canine","Canine"),("feline","Feline"),("equine","Equine"),("bovine","Bovine"),("avian","Avian"),("other","Other")])
    breed = models.CharField(max_length=200, blank=True)
    sex = models.CharField(max_length=20, choices=[("male","Male"),("female","Female"),("male_neutered","Male Neutered"),("female_spayed","Female Spayed")], blank=True)
    color = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    weight_kg = models.DecimalField(max_digits=6, decimal_places=1, null=True, blank=True)
    microchip_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True); updated_at = models.DateTimeField(auto_now=True)
    objects = TenantScopedManager()
    class Meta: db_table = "vet_animal"
    def __str__(self): return f"{self.species} — {self.patient.full_name}"

class RabiesCertificate(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="rabies_certs")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="rabies_certs")
    vaccine_name = models.CharField(max_length=200); lot_number = models.CharField(max_length=100, blank=True)
    administered_date = models.DateField(default=timezone.localdate)
    expiration_date = models.DateField()
    veterinarian = models.CharField(max_length=200, blank=True)
    certificate_number = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = TenantScopedManager()
    class Meta: db_table = "vet_rabies"; ordering = ["-administered_date"]
    def __str__(self): return f"Rabies Cert {self.certificate_number} — {self.patient.full_name}"
