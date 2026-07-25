"""
Permission enforcement for Django REST Framework.

Provides:
    - TenantPermissionRequired: class-level permission check.
    - HasTenantAccess: base permission requiring tenant context.
    - IsTenantAdmin: super admin or tenant admin check.

Usage:
    @extend_schema(...)
    class PatientListView(generics.ListAPIView):
        permission_classes = [TenantPermissionRequired]
        required_permission = "patients.read"
"""
from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied, NotAuthenticated


class HasTenantAccess(BasePermission):
    """
    Require that the request has a resolved tenant.
    Super admins (is_superuser=True) pass without a tenant.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            raise NotAuthenticated("Authentication required.")

        # Super admins can operate cross-tenant
        if request.user.is_superuser:
            return True

        # Regular users must have a tenant
        if not request.tenant:
            raise PermissionDenied(
                "Tenant context is required. Provide X-Tenant-Slug header."
            )

        # User must belong to the resolved tenant
        if request.user.tenant_id != request.tenant.id:
            raise PermissionDenied(
                "You do not belong to this tenant."
            )

        return True


class TenantPermissionRequired(BasePermission):
    """
    Check that the user has a specific permission via their role.

    Set `required_permission` on the view class.
    """

    required_permission: str | None = None

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            raise NotAuthenticated("Authentication required.")

        # Super admins bypass permission checks
        if request.user.is_superuser:
            return True

        # Resolve the required permission
        perm = self._get_required_permission(view)
        if perm is None:
            return True  # No permission required

        if not request.user.has_permission(perm):
            raise PermissionDenied(
                f"Missing required permission: {perm}."
            )

        return True

    def _get_required_permission(self, view) -> str | None:
        """Resolve required permission from view or class attribute."""
        # Allow views to define per-method permissions via get_required_permission()
        if hasattr(view, "get_required_permission"):
            return view.get_required_permission()
        if self.required_permission:
            return self.required_permission
        return getattr(view, "required_permission", None)


class IsTenantAdmin(BasePermission):
    """
    Allow only tenant admins or super admins.
    Checks for 'admin' role or is_superuser flag.
    """

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            raise NotAuthenticated("Authentication required.")

        if request.user.is_superuser:
            return True

        if request.user.role and request.user.role.name.lower() in ("admin", "administrator"):
            return True

        raise PermissionDenied("Tenant admin access required.")
