from .settings import *

DEBUG = False

# Use SQLite for fast, dependency-free testing in CI
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Use in-memory email backend (safe + testable)
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Use in-memory cache instead of Redis
CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-default-cache",
    },
    "otp_cache": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "test-otp-cache",
        "TIMEOUT": 300,
    },
}

# Use in-memory channel layer (no Redis needed for tests)
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

# Speed up tests: faster password hashing
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Celery runs tasks inline — no broker/worker needed in CI
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True