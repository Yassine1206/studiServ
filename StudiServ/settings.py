from pathlib import Path
from datetime import timedelta
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# ⚠️  Change this in production!
SECRET_KEY = "django-insecure-dev-key-change-me"
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # Tiers
    "rest_framework",
    "rest_framework_simplejwt",
    

    # Local
    "marketplace",
    'channels',
    'corsheaders',
    'messaging',
    'administration',
    'chatbot',
    'addons',
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",          # ← doit être en premier
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "StudiServ.urls"

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

WSGI_APPLICATION = "StudiServ.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "studiserv",
        "USER": "studiserv_user",
        "PASSWORD": "Studiserv123!",
        "HOST": "localhost",
        "PORT": "3307",
        "OPTIONS": {
            "charset": "utf8mb4",
        },
    }
}
# WebSocket
ASGI_APPLICATION = 'StudiServ.asgi.application'

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {'hosts': [('127.0.0.1', 6379)]},
    },
}
# Chatbot RAG
CHATBOT_SETTINGS = {
    'OPENAI_API_KEY': os.environ.get('OPENAI_API_KEY', ''),
    'LLM_PROVIDER': os.environ.get('LLM_PROVIDER', 'ollama'),
    'OPENAI_MODEL': 'gpt-3.5-turbo',
    'OLLAMA_BASE_URL': 'http://localhost:11434',
    'OLLAMA_MODEL': 'mistral',
    'CHROMA_PERSIST_DIR': str(BASE_DIR / 'chroma_db'),
    'EMBEDDING_MODEL': 'paraphrase-multilingual-MiniLM-L12-v2',
    'TOP_K_RESULTS': 4,
    'MAX_TOKENS_RESPONSE': 512,
}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Africa/Tunis"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATICFILES_DIRS = [BASE_DIR / "static"]

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ─── Authentification ────────────────────────────────────────────────────────
AUTHENTICATION_BACKENDS = [
    "marketplace.backends.EmailBackend",
    "django.contrib.auth.backends.ModelBackend",
]

# Pour les vues Django classiques (admin, etc.)
LOGIN_URL = "marketplace:login"
LOGIN_REDIRECT_URL = "marketplace:etudiant_dashboard"
LOGOUT_REDIRECT_URL = "marketplace:index"

# ─── Django REST Framework ───────────────────────────────────────────────────
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

# ─── JWT ─────────────────────────────────────────────────────────────────────
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=2),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": False,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ─── CORS ────────────────────────────────────────────────────────────────────
# Autorise le frontend Vite (port 5173) à appeler l'API Django (port 8000)
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
CORS_ALLOW_CREDENTIALS = True
