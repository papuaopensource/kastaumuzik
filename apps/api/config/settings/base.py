"""Settings shared by every environment.

`development` and `production` import from here and override what differs.
Secrets and deployment values are read from the environment.
"""

from pathlib import Path

from decouple import Csv, config
from django.templatetags.static import static
from django.urls import reverse_lazy

# config/settings/base.py -> config/settings -> config -> apps/api
BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config("SECRET_KEY")
DEBUG = config("DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="", cast=Csv())

INSTALLED_APPS = [
    # Unfold must precede django.contrib.admin so its templates win.
    "unfold",
    "unfold.contrib.filters",
    "unfold.contrib.forms",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "django_filters",
    "corsheaders",
    "accounts",
    "catalog",
    "submissions",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    # CORS has to sit above CommonMiddleware so preflight responses still get
    # their headers when CommonMiddleware would otherwise short-circuit.
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

AUTH_USER_MODEL = "accounts.User"

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "id"
TIME_ZONE = "Asia/Jayapura"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "default": {"BACKEND": "django.core.files.storage.FileSystemStorage"},
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage"
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# --- Django REST Framework -------------------------------------------------
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.AllowAny"],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
        "rest_framework.filters.OrderingFilter",
    ],
    "DEFAULT_THROTTLE_CLASSES": ["rest_framework.throttling.ScopedRateThrottle"],
    # Applies to the submission endpoint only; read endpoints are unthrottled.
    # Rejected requests count against the limit.
    "DEFAULT_THROTTLE_RATES": {
        "submission-hour": config("THROTTLE_SUBMISSION_HOUR", default="10/hour"),
        "submission-day": config("THROTTLE_SUBMISSION_DAY", default="30/day"),
    },
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 100,
    "UNAUTHENTICATED_USER": None,
}

# --- CORS ------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = config("CORS_ALLOWED_ORIGINS", default="", cast=Csv())
CORS_ALLOW_METHODS = ["GET", "POST", "OPTIONS"]


# --- Unfold admin ----------------------------------------------------------
def _can(permission: str):
    """Build a sidebar `permission` callback for one permission string."""

    def check(request) -> bool:
        return request.user.has_perm(permission)

    return check


UNFOLD = {
    "SITE_TITLE": "kastaumuzik",
    "SITE_HEADER": "kastaumuzik",
    "SITE_SUBHEADER": "arsip lagu daerah Papua",
    "SITE_URL": "https://kastaumuzik.com",
    "SITE_ICON": lambda request: static("admin-brand/logo.png"),
    "SITE_FAVICONS": [
        {
            "rel": "icon",
            "sizes": "96x96",
            "type": "image/png",
            "href": lambda request: static("admin-brand/favicon-96x96.png"),
        },
        {
            "rel": "icon",
            "type": "image/svg+xml",
            "href": lambda request: static("admin-brand/favicon.svg"),
        },
        {
            "rel": "apple-touch-icon",
            "sizes": "180x180",
            "href": lambda request: static("admin-brand/apple-touch-icon.png"),
        },
    ],
    # Setting THEME locks the appearance and hides the light/dark switcher.
    "THEME": "light",
    # Replaces the default model listing on the admin home page.
    "DASHBOARD_CALLBACK": "catalog.dashboard.callback",
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": False,
    "SHOW_LANGUAGES": False,
    "COLORS": {
        "primary": {
            "50": "255 247 237",
            "100": "255 237 213",
            "200": "254 215 170",
            "300": "253 186 116",
            "400": "251 146 60",
            "500": "249 115 22",
            "600": "234 88 12",
            "700": "194 65 12",
            "800": "154 52 18",
            "900": "124 45 18",
            "950": "67 20 7",
        },
    },
    "LOGIN": {
        "form": "accounts.forms.EmailAuthenticationForm",
    },
    "SIDEBAR": {
        "show_search": True,
        "show_all_applications": False,
        "navigation": [
            {
                "title": "Ringkasan",
                "separator": False,
                "items": [
                    {
                        "title": "Beranda admin",
                        "icon": "home",
                        "link": reverse_lazy("admin:index"),
                    },
                ],
            },
            {
                "title": "Kurasi",
                "separator": True,
                "items": [
                    {
                        "title": "Usulan masuk",
                        "icon": "inbox",
                        "link": reverse_lazy("admin:submissions_submission_changelist"),
                        "permission": _can("submissions.view_submission"),
                    },
                ],
            },
            {
                "title": "Katalog",
                "separator": True,
                "items": [
                    {
                        "title": "Video",
                        "icon": "music_video",
                        "link": reverse_lazy("admin:catalog_video_changelist"),
                        "permission": _can("catalog.view_video"),
                    },
                    {
                        "title": "Koleksi",
                        "icon": "library_music",
                        "link": reverse_lazy("admin:catalog_collection_changelist"),
                        "permission": _can("catalog.view_collection"),
                    },
                    {
                        "title": "Bentuk video",
                        "icon": "movie",
                        "link": reverse_lazy("admin:catalog_format_changelist"),
                        "permission": _can("catalog.view_format"),
                    },
                ],
            },
            {
                "title": "Akses",
                "separator": True,
                "items": [
                    {
                        "title": "Pengguna",
                        "icon": "person",
                        "link": reverse_lazy("admin:accounts_user_changelist"),
                        "permission": _can("accounts.view_user"),
                    },
                    {
                        "title": "Peran",
                        "icon": "shield_person",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                        "permission": _can("auth.view_group"),
                    },
                ],
            },
        ],
    },
}
