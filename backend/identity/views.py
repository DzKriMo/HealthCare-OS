"""
Authentication views: login, refresh, logout, MFA, password management,
session management, role/permission management.

All views are tenant-aware. Auth endpoints (login, refresh) bypass tenant
middleware. Management endpoints require tenant context.
"""
from django.utils import timezone
from rest_framework import generics, permissions, status, views
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from drf_spectacular.utils import extend_schema, OpenApiExample

from tenancy.permissions import HasTenantAccess, TenantPermissionRequired, IsTenantAdmin
from .models import User, Role, Permission, UserSession
from . import serializers


# ═══════════════════════════════════════════════════════════════
# Auth — Login, Refresh, Logout
# ═══════════════════════════════════════════════════════════════

@extend_schema(
    tags=["auth"],
    summary="Login",
    description="Authenticate with email, password, and tenant. Returns JWT tokens.",
    request=serializers.LoginSerializer,
    examples=[
        OpenApiExample(
            "Login example",
            value={
                "email": "doctor@smileclinic.com",
                "password": "securepassword",
                "tenant_slug": "smile-dental",
                "device_type": "web",
            },
        ),
    ],
)
class LoginView(generics.GenericAPIView):
    """Login — obtain JWT access and refresh tokens."""

    serializer_class = serializers.LoginSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = self.get_serializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)

        return Response({
            "user": serializers.UserSerializer(serializer.validated_data["user"]).data,
            "tokens": serializer.validated_data["tokens"],
            "session_id": serializer.validated_data["session_id"],
            "requires_mfa": serializer.validated_data["user"].mfa_enabled,
        })


@extend_schema(tags=["auth"], summary="Refresh access token")
class TokenRefreshView(generics.GenericAPIView):
    """Refresh — get a new access token using a valid refresh token."""

    serializer_class = serializers.TokenRefreshSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


@extend_schema(tags=["auth"], summary="Logout")
class LogoutView(generics.GenericAPIView):
    """Logout — blacklist the refresh token. Requires authentication."""

    serializer_class = serializers.LogoutSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


# ═══════════════════════════════════════════════════════════════
# MFA
# ═══════════════════════════════════════════════════════════════

@extend_schema(tags=["auth"], summary="Setup MFA (TOTP)")
class MFASetupView(generics.GenericAPIView):
    """Initiate MFA setup — returns TOTP secret and QR code URI."""

    serializer_class = serializers.MFASetupSerializer

    def post(self, request):
        serializer = self.get_serializer(data={})
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


@extend_schema(tags=["auth"], summary="Confirm MFA setup")
class MFAConfirmView(generics.GenericAPIView):
    """Confirm MFA setup by verifying a TOTP code."""

    serializer_class = serializers.MFAConfirmSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


@extend_schema(tags=["auth"], summary="Disable MFA")
class MFADisableView(generics.GenericAPIView):
    """Disable MFA — requires current TOTP code."""

    serializer_class = serializers.MFADisableSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data)


# ═══════════════════════════════════════════════════════════════
# Password Management
# ═══════════════════════════════════════════════════════════════

@extend_schema(tags=["auth"], summary="Change password (authenticated)")
class PasswordChangeView(generics.GenericAPIView):
    """Change password while authenticated."""

    serializer_class = serializers.PasswordChangeSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # Revoke all other sessions (security best practice after password change)
        UserSession.objects.filter(user=request.user).exclude(
            id=self._current_session_id(request),
        ).update(revoked_at=timezone.now())
        return Response({"detail": "Password changed successfully."})

    def _current_session_id(self, request):
        # Extract current session from the JWT
        if request.auth:
            return request.auth.get("jti")
        return None


@extend_schema(
    tags=["auth"],
    summary="Request password reset",
)
class PasswordResetRequestView(generics.GenericAPIView):
    """Request a password reset link via email."""

    serializer_class = serializers.PasswordResetRequestSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"detail": serializer.validated_data["detail"]})


@extend_schema(tags=["auth"], summary="Confirm password reset")
class PasswordResetConfirmView(generics.GenericAPIView):
    """Confirm password reset with one-time token."""

    serializer_class = serializers.PasswordResetConfirmSerializer
    permission_classes = [permissions.AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({"detail": serializer.validated_data["detail"]})


# ═══════════════════════════════════════════════════════════════
# Session Management
# ═══════════════════════════════════════════════════════════════

@extend_schema(tags=["auth"], summary="List active sessions")
class SessionListView(generics.ListAPIView):
    """List the current user's active sessions."""

    serializer_class = serializers.SessionSerializer

    def get_queryset(self):
        return (
            UserSession.objects
            .filter(user=self.request.user, revoked_at__isnull=True)
            .order_by("-created_at")
        )

    ordering = ["-created_at"]


@extend_schema(tags=["auth"], summary="Revoke session(s)")
class SessionRevokeView(generics.GenericAPIView):
    """Revoke a specific session, or all other sessions."""

    serializer_class = serializers.SessionRevokeSerializer

    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        session_id = serializer.validated_data.get("session_id")
        revoke_all = serializer.validated_data.get("revoke_all")

        queryset = UserSession.objects.filter(user=request.user)

        if revoke_all:
            # Revoke all sessions except the current one
            current_jti = request.auth.get("jti") if request.auth else None
            to_revoke = queryset.exclude(refresh_token_jti=current_jti)
            count = to_revoke.update(revoked_at=timezone.now())
            return Response({"detail": f"Revoked {count} session(s)."})

        if session_id:
            try:
                session = queryset.get(id=session_id)
                session.revoke()
                return Response({"detail": "Session revoked."})
            except UserSession.DoesNotExist:
                return Response(
                    {"error": "Session not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        return Response(
            {"error": "Provide session_id or set revoke_all=true."},
            status=status.HTTP_400_BAD_REQUEST,
        )


# ═══════════════════════════════════════════════════════════════
# Role & Permission Management
# ═══════════════════════════════════════════════════════════════

@extend_schema(tags=["roles"], summary="List roles")
class RoleListView(generics.ListCreateAPIView):
    """List all roles for the current tenant, or create a new one."""

    serializer_class = serializers.RoleSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "identity.manage_roles"

    def get_queryset(self):
        qs = Role.objects.filter(tenant=self.request.tenant)
        # Include system roles as templates
        system_roles = Role.objects.filter(is_system_role=True)
        return (qs | system_roles).distinct().order_by("name")

    def perform_create(self, serializer):
        serializer.save()


@extend_schema(tags=["roles"], summary="Manage role")
class RoleDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete a role."""

    serializer_class = serializers.RoleSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "identity.manage_roles"

    def get_queryset(self):
        # Include tenant-scoped roles AND system roles for viewing
        qs = Role.objects.filter(tenant=self.request.tenant)
        system_roles = Role.objects.filter(is_system_role=True)
        return (qs | system_roles).distinct().order_by("name")

    def perform_destroy(self, instance):
        if instance.is_system_role:
            raise PermissionDenied("System roles cannot be deleted.")
        instance.delete()


@extend_schema(tags=["roles"], summary="List all available permissions")
class PermissionListView(generics.ListAPIView):
    """List all permissions available in the system (read-only)."""

    serializer_class = serializers.PermissionSerializer
    permission_classes = [HasTenantAccess]

    def get_queryset(self):
        return Permission.objects.all().order_by("resource", "action")


# ═══════════════════════════════════════════════════════════════
# User Management
# ═══════════════════════════════════════════════════════════════

@extend_schema(tags=["users"], summary="List users")
class UserListView(generics.ListCreateAPIView):
    """List all users for the current tenant, or create a new one."""

    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "identity.manage_users"

    def get_serializer_class(self):
        if self.request.method == "POST":
            return serializers.UserCreateSerializer
        return serializers.UserSerializer

    def get_queryset(self):
        return User.objects.filter(
            tenant=self.request.tenant, is_active=True,
        ).select_related("role").order_by("last_name", "first_name")

    ordering = ["last_name", "first_name"]

    def perform_create(self, serializer):
        serializer.save()


@extend_schema(tags=["users"], summary="Manage user")
class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or deactivate a user."""

    serializer_class = serializers.UserSerializer
    permission_classes = [HasTenantAccess, TenantPermissionRequired]
    required_permission = "identity.manage_users"

    def get_queryset(self):
        return User.objects.filter(tenant=self.request.tenant)

    def perform_destroy(self, instance):
        # Soft-deactivate rather than hard-delete
        instance.is_active = False
        instance.save(update_fields=["is_active"])
        # Revoke all sessions
        UserSession.objects.filter(user=instance).update(
            revoked_at=timezone.now(),
        )


@extend_schema(tags=["users"], summary="Get current user profile")
class CurrentUserView(generics.RetrieveAPIView):
    """Return the authenticated user's profile."""

    serializer_class = serializers.UserSerializer

    def get_object(self):
        return self.request.user
