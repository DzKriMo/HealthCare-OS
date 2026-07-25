"""
Custom authentication backend that uses email + password.

Django's default UserManager + authenticate works with USERNAME_FIELD=email,
but we make it explicit here for clarity and future extensibility (e.g.,
tenant-aware authentication, rate limiting, MFA checks).
"""
from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model

User = get_user_model()


class EmailBackend(BaseBackend):
    """
    Authenticate using email and password.

    This is largely handled by Django's ModelBackend since we set
    USERNAME_FIELD = 'email', but this explicit backend allows
    future tenant-aware or MFA-gated authentication logic.
    """

    def authenticate(self, request, email=None, password=None, **kwargs):
        if email is None or password is None:
            return None

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Run password hasher anyway to prevent timing attacks
            User().set_password(password)
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None

    def user_can_authenticate(self, user):
        return user.is_active

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
