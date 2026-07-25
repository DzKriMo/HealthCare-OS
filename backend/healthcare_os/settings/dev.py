"""
Development settings — local Docker Compose environment.
"""
from .base import *  # noqa: F403

SECRET_KEY = os.environ.get(  # noqa: F405
    "SECRET_KEY", "dev-secret-key-change-in-production-xxxxxxxxxxxx"
)

DEBUG = True

ALLOWED_HOSTS = ["*"]

# CORS — allow all origins in dev
CORS_ALLOW_ALL_ORIGINS = True

# SimpleJWT signing key
SIMPLE_JWT["SIGNING_KEY"] = SECRET_KEY  # noqa: F405

# Email — console backend for dev
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# MinIO / S3 for dev (local MinIO container)
AWS_ACCESS_KEY_ID = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")  # noqa: F405
AWS_SECRET_ACCESS_KEY = os.environ.get("MINIO_SECRET_KEY", "minioadmin")  # noqa: F405
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME", "healthcare-os-dev")  # noqa: F405
AWS_S3_ENDPOINT_URL = os.environ.get("AWS_S3_ENDPOINT_URL", "http://localhost:9000")  # noqa: F405
AWS_S3_REGION_NAME = "us-east-1"
AWS_S3_SIGNATURE_VERSION = "s3v4"
AWS_DEFAULT_ACL = "private"

# File storage
STORAGES = {
    "default": {
        "BACKEND": "storages.backends.s3.S3Storage",
        "OPTIONS": {
            "access_key": AWS_ACCESS_KEY_ID,
            "secret_key": AWS_SECRET_ACCESS_KEY,
            "bucket_name": AWS_STORAGE_BUCKET_NAME,
            "endpoint_url": AWS_S3_ENDPOINT_URL,
            "region_name": AWS_S3_REGION_NAME,
            "signature_version": AWS_S3_SIGNATURE_VERSION,
            "default_acl": AWS_DEFAULT_ACL,
            "custom_domain": False,
            "querystring_auth": True,
            "url_protocol": "http:",
        },
    },
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}

# Debug toolbar
if DEBUG:
    INSTALLED_APPS += ["django_extensions"]  # noqa: F405
