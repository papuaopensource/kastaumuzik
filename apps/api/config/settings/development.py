"""Local development settings. Plain SQLite, no PRAGMA tuning."""

from .base import *  # noqa: F403
from .base import BASE_DIR, Csv, config

DEBUG = config("DEBUG", default=True, cast=bool)

# A leading dot covers "localhost" and every subdomain of it.
ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default=".localhost,127.0.0.1,[::1]",
    cast=Csv(),
)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": config("DATABASE_PATH", default=BASE_DIR / "db.sqlite3"),
    }
}

CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:4321,http://127.0.0.1:4321",
    cast=Csv(),
)

# Development only; production uses the explicit allowlist above.
CORS_ALLOWED_ORIGIN_REGEXES = [r"^http://([a-z0-9-]+\.)*localhost(:\d+)?$"]

MAILERS = {
    "default": {"BACKEND": "django.core.mail.backends.console.EmailBackend"},
}
