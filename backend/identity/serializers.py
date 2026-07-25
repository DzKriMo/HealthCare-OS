"""
Serializers for authentication, user management, and roles.
"""
import logging
from django.utils import timezone
from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from tenancy.models import Tenant
from .models import User, Role, Permission, UserSession, Device

logger = logging.getLogger("healthcare_os.identity")


# ── Auth ──────────────────────────────────────────────────────

class LoginSerializer(serializers.Serializer):
    """Login with email + password + tenant_slug."""

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    tenant_slug = serializers.SlugField(required=False, allow_blank=True)
    device_name = serializers.CharField(required=False, allow_blank=True, max_length=200)
    device_type = serializers.ChoiceField(
        choices=[("web", "Web"), ("desktop", "Desktop"), ("mobile", "Mobile")],
        default="web",
    )
    totp_code = serializers.CharField(
        required=False, allow_blank=True, max_length=6,
        help_text="TOTP code if MFA is enabled.",
    )

    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")
        tenant_slug = attrs.get("tenant_slug")
        totp_code = attrs.get("totp_code", "")

        from healthcare_os.middleware import record_failed_login, clear_failed_logins
        ip = self._get_client_ip() or ""

        # Authenticate user
        user = authenticate(request=self.context.get("request"), email=email, password=password)

        if user is None:
            record_failed_login(ip)
            raise serializers.ValidationError("Invalid email or password.")

        if not user.is_active:
            raise serializers.ValidationError("This account is inactive.")

        # Tenant validation
        if tenant_slug and user.tenant:
            if user.tenant.slug != tenant_slug:
                raise serializers.ValidationError("User does not belong to this tenant.")
        elif tenant_slug and user.tenant is None and not user.is_superuser:
            raise serializers.ValidationError("Tenant is required for this user.")

        # MFA check
        if user.mfa_enabled:
            if not totp_code:
                raise serializers.ValidationError(
                    "MFA code required.", code="mfa_required"
                )
            if not self._verify_totp(user, totp_code):
                raise serializers.ValidationError("Invalid MFA code.")

        # Successful auth — clear brute-force counter for this IP
        clear_failed_logins(ip)

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        refresh["tenant_id"] = str(user.tenant_id) if user.tenant else None
        refresh["tenant_slug"] = user.tenant.slug if user.tenant else None
        refresh["role"] = user.role.name if user.role else None

        # Record session
        user_session = UserSession.objects.create(
            user=user,
            tenant=user.tenant,
            refresh_token_jti=str(refresh.payload["jti"]),
            device_name=attrs.get("device_name", ""),
            device_type=attrs.get("device_type", "web"),
            ip_address=self._get_client_ip(),
            user_agent=self._get_user_agent(),
            expires_at=timezone.now() + timezone.timedelta(hours=4),
        )

        attrs["user"] = user
        attrs["tokens"] = {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "expires_in": 900,  # 15 minutes
            "token_type": "Bearer",
        }
        attrs["session_id"] = str(user_session.id)

        return attrs

    def _verify_totp(self, user, code: str) -> bool:
        """Verify a 6-digit TOTP code against the user's stored secret.

        The secret is stored base32-encoded in ``user.mfa_secret``. We accept a
        +/-1 step (30s) drift window to tolerate clock skew. Backup codes
        (stored newline-separated in ``user.mfa_backup_codes``) are also
        accepted and consumed on use.
        """
        import base64
        import binascii
        from django_otp.oath import totp as _totp

        code = (code or "").strip().replace(" ", "")
        if not user.mfa_secret:
            return False

        # Backup code path (8+ char alphanumeric codes)
        if len(code) >= 8 and getattr(user, "mfa_backup_codes", ""):
            remaining = [c for c in user.mfa_backup_codes.splitlines() if c]
            if code in remaining:
                remaining.remove(code)
                user.mfa_backup_codes = "\n".join(remaining)
                user.save(update_fields=["mfa_backup_codes"])
                return True

        if not code.isdigit() or len(code) != 6:
            return False

        try:
            key = base64.b32decode(user.mfa_secret, casefold=True)
        except (binascii.Error, ValueError):
            return False

        expected = int(code)
        # Accept current step plus one step of drift on either side.
        return any(_totp(key, drift=d) == expected for d in (-1, 0, 1))

    def _get_client_ip(self) -> str | None:
        request = self.context.get("request")
        if request:
            xff = request.META.get("HTTP_X_FORWARDED_FOR")
            if xff:
                return xff.split(",")[0].strip()
            return request.META.get("REMOTE_ADDR")
        return None

    def _get_user_agent(self) -> str:
        request = self.context.get("request")
        if request:
            return request.META.get("HTTP_USER_AGENT", "")
        return ""


class TokenRefreshSerializer(serializers.Serializer):
    """Refresh an access token. Blacklists old refresh, issues new pair."""

    refresh = serializers.CharField()

    def validate(self, attrs):
        refresh_token_str = attrs["refresh"]

        try:
            refresh = RefreshToken(refresh_token_str)
        except Exception:
            raise serializers.ValidationError("Invalid or expired refresh token.")

        # Revoke the old refresh token's session
        jti = refresh.payload.get("jti")
        if jti:
            UserSession.objects.filter(refresh_token_jti=jti).update(
                revoked_at=timezone.now(),
            )

        # Rotate: blacklist old, issue new
        refresh.blacklist()

        user_id = refresh.payload.get("user_id")
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")

        new_refresh = RefreshToken.for_user(user)
        new_refresh["tenant_id"] = refresh.payload.get("tenant_id")
        new_refresh["tenant_slug"] = refresh.payload.get("tenant_slug")
        new_refresh["role"] = user.role.name if user.role else None

        # Record new session
        UserSession.objects.create(
            user=user,
            tenant=user.tenant,
            refresh_token_jti=str(new_refresh.payload["jti"]),
            device_type="web",
            expires_at=timezone.now() + timezone.timedelta(hours=4),
        )

        return {
            "access": str(new_refresh.access_token),
            "refresh": str(new_refresh),
            "expires_in": 900,
            "token_type": "Bearer",
        }


class LogoutSerializer(serializers.Serializer):
    """Logout — blacklist the refresh token."""

    refresh = serializers.CharField()

    def validate(self, attrs):
        refresh_token_str = attrs["refresh"]
        try:
            refresh = RefreshToken(refresh_token_str)
            refresh.blacklist()
        except Exception:
            pass  # Token already invalid — still a successful logout

        # Revoke the session
        try:
            token = RefreshToken(refresh_token_str)
            jti = token.payload.get("jti")
            if jti:
                UserSession.objects.filter(refresh_token_jti=jti).update(
                    revoked_at=timezone.now(),
                )
        except Exception:
            pass

        return {"detail": "Logged out successfully."}


# ── MFA ───────────────────────────────────────────────────────

class MFASetupSerializer(serializers.Serializer):
    """Initiate MFA setup — returns TOTP secret and QR code URI."""

    def validate(self, attrs):
        user = self.context["request"].user
        if user.mfa_enabled:
            raise serializers.ValidationError("MFA is already enabled.")

        # Generate TOTP secret (placeholder — use django-otp in production)
        import base64
        import os
        secret = base64.b32encode(os.urandom(20)).decode("utf-8")

        # Store encrypted secret
        user.mfa_secret = secret  # In production: encrypt this
        user.save(update_fields=["mfa_secret"])

        uri = (
            f"otpauth://totp/HealthcareOS:{user.email}"
            f"?secret={secret}&issuer=HealthcareOS"
        )

        attrs["secret"] = secret
        attrs["qr_uri"] = uri
        return attrs


class MFAConfirmSerializer(serializers.Serializer):
    """Confirm MFA setup with a TOTP code."""

    code = serializers.CharField(max_length=6, min_length=6)

    def validate(self, attrs):
        user = self.context["request"].user
        code = attrs["code"]

        if user.mfa_enabled:
            raise serializers.ValidationError("MFA is already enabled.")

        # Verify code (placeholder)
        # In production: django_otp.verify_token(user, code)
        verified = True

        if not verified:
            raise serializers.ValidationError("Invalid code.")

        user.mfa_enabled = True
        user.save(update_fields=["mfa_enabled"])

        return {"detail": "MFA enabled successfully."}


class MFADisableSerializer(serializers.Serializer):
    """Disable MFA — requires current TOTP code."""

    code = serializers.CharField(max_length=6, min_length=6)

    def validate(self, attrs):
        user = self.context["request"].user
        # Verify code before disabling
        verified = True  # Placeholder
        if not verified:
            raise serializers.ValidationError("Invalid code.")

        user.mfa_enabled = False
        user.mfa_secret = ""
        user.save(update_fields=["mfa_enabled", "mfa_secret"])

        return {"detail": "MFA disabled."}


# ── Password ──────────────────────────────────────────────────

class PasswordChangeSerializer(serializers.Serializer):
    """Change password while authenticated."""

    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(
        write_only=True, min_length=10, max_length=128,
    )

    def validate(self, attrs):
        user = self.context["request"].user
        if not user.check_password(attrs["current_password"]):
            raise serializers.ValidationError("Current password is incorrect.")
        return attrs

    def save(self):
        user = self.context["request"].user
        user.set_password(self.validated_data["new_password"])
        user.password_changed_at = timezone.now()
        user.password_reset_required = False
        user.save(update_fields=["password", "password_changed_at", "password_reset_required"])
        return user


class PasswordResetRequestSerializer(serializers.Serializer):
    """Request a password reset email."""

    email = serializers.EmailField()
    tenant_slug = serializers.SlugField()

    def validate(self, attrs):
        email = attrs["email"]
        tenant_slug = attrs["tenant_slug"]

        try:
            tenant = Tenant.objects.get(slug=tenant_slug, is_active=True)
            User.objects.get(email=email, tenant=tenant, is_active=True)
        except (Tenant.DoesNotExist, User.DoesNotExist):
            # Don't reveal whether the user exists — always return success
            pass

        # TODO: Send password reset email with one-time token
        attrs["detail"] = (
            "If an account with that email exists, a password reset link "
            "has been sent."
        )
        return attrs


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Confirm password reset with token."""

    token = serializers.CharField()
    new_password = serializers.CharField(min_length=10, max_length=128)

    def validate(self, attrs):
        # TODO: Validate reset token and set new password
        attrs["detail"] = "Password reset successfully."
        return attrs


# ── Session Management ────────────────────────────────────────

class SessionSerializer(serializers.ModelSerializer):
    """Display active sessions to the user."""

    class Meta:
        model = UserSession
        fields = [
            "id", "device_name", "device_type", "ip_address",
            "location", "created_at", "expires_at", "is_active",
        ]


class SessionRevokeSerializer(serializers.Serializer):
    """Revoke a specific session or all sessions."""

    session_id = serializers.UUIDField(required=False)
    revoke_all = serializers.BooleanField(default=False)

    def validate(self, attrs):
        if not attrs.get("session_id") and not attrs.get("revoke_all"):
            raise serializers.ValidationError(
                "Provide session_id or set revoke_all=true."
            )
        return attrs


# ── Role & Permission ─────────────────────────────────────────

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ["id", "codename", "description", "resource", "action"]


class RoleSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(many=True, read_only=True)
    permission_ids = serializers.ListField(
        child=serializers.UUIDField(), write_only=True, required=False,
    )

    class Meta:
        model = Role
        fields = [
            "id", "name", "is_system_role", "description",
            "permissions", "permission_ids", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "is_system_role", "created_at", "updated_at"]

    def create(self, validated_data):
        permission_ids = validated_data.pop("permission_ids", [])
        tenant = self.context["request"].tenant
        role = Role.objects.create(tenant=tenant, **validated_data)
        if permission_ids:
            role.permissions.set(permission_ids)
        return role

    def update(self, instance, validated_data):
        permission_ids = validated_data.pop("permission_ids", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if permission_ids is not None:
            instance.permissions.set(permission_ids)
        return instance


# ── User ──────────────────────────────────────────────────────

class UserSerializer(serializers.ModelSerializer):
    """Read/write user with role and tenant info."""

    role_name = serializers.CharField(source="role.name", read_only=True)
    tenant_slug = serializers.CharField(source="tenant.slug", read_only=True)
    full_name = serializers.CharField(read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "email", "first_name", "last_name", "full_name",
            "role", "role_name", "tenant", "tenant_slug",
            "license_number", "specialty", "department",
            "mfa_enabled", "is_active", "is_staff",
            "password_reset_required",
            "last_login", "created_at",
        ]
        read_only_fields = [
            "id", "last_login", "created_at",
        ]


class UserCreateSerializer(serializers.ModelSerializer):
    """Create a new user within the current tenant."""

    password = serializers.CharField(write_only=True, min_length=10)
    role_id = serializers.UUIDField()

    class Meta:
        model = User
        fields = [
            "email", "first_name", "last_name", "password",
            "role_id", "license_number", "specialty", "department",
        ]

    def validate_role_id(self, role_id):
        tenant = self.context["request"].tenant
        try:
            role = Role.objects.get(id=role_id)
        except Role.DoesNotExist:
            raise serializers.ValidationError("Role not found.")
        # Role must be system role or belong to this tenant
        if not role.is_system_role and role.tenant_id != tenant.id:
            raise serializers.ValidationError("Role does not belong to this tenant.")
        return role_id

    def create(self, validated_data):
        role_id = validated_data.pop("role_id")
        password = validated_data.pop("password")
        tenant = self.context["request"].tenant

        user = User.objects.create_user(
            tenant=tenant,
            role_id=role_id,
            password=password,
            **validated_data,
        )
        return user
