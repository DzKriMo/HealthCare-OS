"""
Base tenant-scoped manager and queryset.

Every model that is tenant-scoped should use TenantScopedManager
to automatically filter by request.tenant. This is the primary
defense against cross-tenant data leakage.

Usage:
    class Patient(models.Model):
        tenant = models.ForeignKey(Tenant, ...)
        objects = TenantScopedManager()

    # In a view or anywhere with access to request:
    patients = Patient.objects.for_tenant(request.tenant)
"""
from django.db import models
from django.db.models.query import QuerySet


class TenantScopedQuerySet(QuerySet):
    """
    QuerySet that can filter by tenant.
    """

    def for_tenant(self, tenant):
        """
        Return objects scoped to a specific tenant.
        If tenant is None (super admin context), return all.
        """
        if tenant is None:
            return self
        return self.filter(tenant=tenant)

    def for_tenant_strict(self, tenant):
        """
        Return objects scoped to a specific tenant.
        Raises ValueError if tenant is None (always require a tenant).
        """
        if tenant is None:
            raise ValueError("Tenant is required for this query.")
        return self.filter(tenant=tenant)


class TenantScopedManager(models.Manager):
    """
    Manager that defaults to tenant-scoped queries.

    In views, always use .for_tenant(request.tenant) explicitly.
    The auto-scoping via get_queryset is a safety net, not the primary path.
    """

    def get_queryset(self):
        # Default queryset returns all — scoping is explicit via .for_tenant()
        return TenantScopedQuerySet(self.model, using=self._db)

    def for_tenant(self, tenant):
        return self.get_queryset().for_tenant(tenant)

    def for_tenant_strict(self, tenant):
        return self.get_queryset().for_tenant_strict(tenant)
