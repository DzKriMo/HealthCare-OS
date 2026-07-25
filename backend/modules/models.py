"""Module registry models — Sprint 7."""
from django.db import models


class ModuleInstallation(models.Model):
    """Track which modules are installed/enabled per tenant."""

    class Meta:
        db_table = "modules_installation"
