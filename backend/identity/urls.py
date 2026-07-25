"""
Identity URLs: Auth, MFA, Passwords, Sessions, Roles, Users.
"""
from django.urls import path
from . import views

app_name = "identity"

urlpatterns = [
    # ── Auth ──────────────────────────────────────────────
    path("login/", views.LoginView.as_view(), name="login"),
    path("token/refresh/", views.TokenRefreshView.as_view(), name="token-refresh"),
    path("logout/", views.LogoutView.as_view(), name="logout"),

    # ── MFA ───────────────────────────────────────────────
    path("mfa/setup/", views.MFASetupView.as_view(), name="mfa-setup"),
    path("mfa/confirm/", views.MFAConfirmView.as_view(), name="mfa-confirm"),
    path("mfa/disable/", views.MFADisableView.as_view(), name="mfa-disable"),

    # ── Password ──────────────────────────────────────────
    path("password/change/", views.PasswordChangeView.as_view(), name="password-change"),
    path(
        "password/reset/",
        views.PasswordResetRequestView.as_view(),
        name="password-reset-request",
    ),
    path(
        "password/reset/confirm/",
        views.PasswordResetConfirmView.as_view(),
        name="password-reset-confirm",
    ),

    # ── Sessions ──────────────────────────────────────────
    path("sessions/", views.SessionListView.as_view(), name="session-list"),
    path("sessions/revoke/", views.SessionRevokeView.as_view(), name="session-revoke"),

    # ── Roles & Permissions ───────────────────────────────
    path("roles/", views.RoleListView.as_view(), name="role-list"),
    path("roles/<uuid:pk>/", views.RoleDetailView.as_view(), name="role-detail"),
    path("permissions/", views.PermissionListView.as_view(), name="permission-list"),

    # ── Users ─────────────────────────────────────────────
    path("users/", views.UserListView.as_view(), name="user-list"),
    path("users/me/", views.CurrentUserView.as_view(), name="current-user"),
    path("users/<uuid:pk>/", views.UserDetailView.as_view(), name="user-detail"),
]
