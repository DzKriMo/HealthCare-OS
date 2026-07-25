"""
Base settings shared across all environments.
"""
import os
from datetime import timedelta
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent.parent

# ── Application definition ─────────────────────────────────
DJANGO_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
]

THIRD_PARTY_APPS = [
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    "django_filters",
    "drf_spectacular",
    "django_otp",
    "django_otp.plugins.otp_totp",
    "channels",
    "storages",
]

LOCAL_APPS = [
    "identity",
    "tenancy",
    "patients",
    "scheduling",
    "billing",
    "documents",
    "notifications",
    "reporting",
    "audit",
    "modules",
    "integrations",
    "inventory",
    "pharmacy",
    "laboratory",
    "imaging",
    "clinical",
    "dermatology",
    "ophthalmology",
    "cardiology",
    "pediatrics",
    "gynecology",
    "orthopedics",
    "ent",
    "physiotherapy",
    "dialysis",
    "oncology",
    "emergency",
    "veterinary",
    "fhir",
    "sync",
    "telemedicine",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "healthcare_os.middleware.StructuredLoggingMiddleware",
    "healthcare_os.middleware.SecurityHeadersMiddleware",
    "healthcare_os.middleware.BruteForceMiddleware",
    "healthcare_os.middleware.RateLimitMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "tenancy.middleware.TenantMiddleware",
    "audit.middleware.AuditMiddleware",
]

ROOT_URLCONF = "healthcare_os.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "healthcare_os.wsgi.application"
ASGI_APPLICATION = "healthcare_os.asgi.application"

# ── Database ───────────────────────────────────────────────
DATABASE_URL = os.environ.get("DATABASE_URL", "")
if DATABASE_URL:
    import dj_database_url
    DATABASES = {"default": dj_database_url.parse(DATABASE_URL)}
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("DB_NAME", "healthcare_os"),
            "USER": os.environ.get("DB_USER", "healthcare_os"),
            "PASSWORD": os.environ.get("DB_PASSWORD", "healthcare_os"),
            "HOST": os.environ.get("DB_HOST", "localhost"),
            "PORT": os.environ.get("DB_PORT", "5432"),
            "CONN_MAX_AGE": 60,
            "OPTIONS": {
                "application_name": "healthcare_os",
            },
        }
    }

# ── Redis / Cache ──────────────────────────────────────────
REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": f"{REDIS_URL}/1",
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    }
}

# ── Celery ─────────────────────────────────────────────────
CELERY_BROKER_URL = f"{REDIS_URL}/2"
CELERY_RESULT_BACKEND = f"{REDIS_URL}/3"
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "UTC"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes

# ── Channels ───────────────────────────────────────────────
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [REDIS_URL],
        },
    },
}

# ── Authentication ─────────────────────────────────────────
AUTH_USER_MODEL = "identity.User"

AUTHENTICATION_BACKENDS = [
    "identity.backends.EmailBackend",
    "django.contrib.auth.backends.ModelBackend",
]

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator", "OPTIONS": {"min_length": 10}},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.Argon2PasswordHasher",
    "django.contrib.auth.hashers.PBKDF2PasswordHasher",
]

# ── JWT (SimpleJWT) ────────────────────────────────────────
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(hours=4),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": None,  # Set from SECRET_KEY per environment
    "AUDIENCE": "healthcare-os",
    "ISSUER": "healthcare-os",
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
}

# ── DRF ────────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.SearchFilter",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    "EXCEPTION_HANDLER": "healthcare_os.utils.exceptions.custom_exception_handler",
}

# ── DRF Spectacular (OpenAPI) ──────────────────────────────
SPECTACULAR_SETTINGS = {
    "TITLE": "Healthcare OS API",
    "DESCRIPTION": "Modular, offline-first, multi-tenant healthcare platform API",
    "VERSION": "0.1.0",
    "SERVE_INCLUDE_SCHEMA": False,
    "SCHEMA_PATH_PREFIX": "/api/",
    "TAGS": [
        {"name": "auth", "description": "Authentication and token management"},
        {"name": "tenants", "description": "Tenant management"},
        {"name": "patients", "description": "Patient master data"},
        {"name": "appointments", "description": "Appointment and scheduling"},
        {"name": "billing", "description": "Billing, invoices, and payments"},
        {"name": "documents", "description": "File storage and document management"},
        {"name": "notifications", "description": "Notification orchestration"},
        {"name": "reports", "description": "Reports and dashboards"},
        {"name": "audit", "description": "Audit logs"},
        {"name": "modules", "description": "Module registry"},
        {"name": "sync", "description": "Offline sync engine"},
    ],
}

# ── Internationalization ───────────────────────────────────
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

# ── Static & Media ─────────────────────────────────────────
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# ── Default primary key field ──────────────────────────────
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ── Security defaults (overridden per environment) ─────────
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"

# ── Logging ────────────────────────────────────────────────
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "format": "[%(asctime)s] %(levelname)s [%(name)s] %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
    "loggers": {
        "django": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
        "healthcare_os": {
            "handlers": ["console"],
            "level": "INFO",
            "propagate": False,
        },
    },
}
