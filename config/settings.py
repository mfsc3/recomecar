# config/settings.py
from pathlib import Path
import os
import sys
from datetime import timedelta

import dj_database_url
from decouple import Csv, config
from django.core.exceptions import ImproperlyConfigured


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
PRODUCAO = not DEBUG and 'test' not in sys.argv


def exigir(nome):
    valor = config(nome, default='')
    if PRODUCAO and not str(valor).strip():
        raise ImproperlyConfigured(
            f'Variável de ambiente obrigatória ausente em produção: {nome}'
        )
    return valor


if PRODUCAO and (
    len(SECRET_KEY) < 50 or SECRET_KEY.startswith('django-insecure')
):
    raise ImproperlyConfigured(
        'SECRET_KEY de produção deve ter pelo menos 50 caracteres.'
    )


ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='', cast=Csv())
RENDER_EXTERNAL_HOSTNAME = os.environ.get('RENDER_EXTERNAL_HOSTNAME', '').strip()
if RENDER_EXTERNAL_HOSTNAME and RENDER_EXTERNAL_HOSTNAME not in ALLOWED_HOSTS:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

CSRF_TRUSTED_ORIGINS = config(
    'CSRF_TRUSTED_ORIGINS',
    default='',
    cast=Csv(),
)
if RENDER_EXTERNAL_HOSTNAME:
    render_origin = f'https://{RENDER_EXTERNAL_HOSTNAME}'
    if render_origin not in CSRF_TRUSTED_ORIGINS:
        CSRF_TRUSTED_ORIGINS.append(render_origin)

INSTALLED_APPS = [
    'django.contrib.admin',
    'csp',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.sites',
    'django.contrib.staticfiles',
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    'axes',
    'accounts',
    'vagas',
    'vitrine',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'csp.middleware.CSPMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'allauth.account.middleware.AccountMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'axes.middleware.AxesMiddleware',
]

ROOT_URLCONF = 'config.urls'
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
WSGI_APPLICATION = 'config.wsgi.application'

SITE_ID = 1
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
    'django.contrib.auth.backends.ModelBackend',
]

DATABASE_URL = config('DATABASE_URL')
DATABASES = {
    'default': dj_database_url.config(
        default=DATABASE_URL,
        conn_max_age=60,
        conn_health_checks=True,
        ssl_require=PRODUCAO and DATABASE_URL.startswith(
            ('postgres://', 'postgresql://')
        ),
    ),
}

PASSWORD_RESET_TIMEOUT = 3600

ACCOUNT_USER_MODEL_USERNAME_FIELD = None
ACCOUNT_USER_MODEL_EMAIL_FIELD = 'email'
ACCOUNT_LOGIN_METHODS = {'email'}
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']
ACCOUNT_EMAIL_VERIFICATION = 'mandatory'
ACCOUNT_EMAIL_CONFIRMATION_EXPIRE_DAYS = 3
ACCOUNT_EMAIL_CONFIRMATION_HMAC = True
ACCOUNT_CONFIRM_EMAIL_ON_GET = False
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = False
ACCOUNT_RATE_LIMITS = {
    'confirm_email': '1/180s/key',
}
ACCOUNT_LOGOUT_ON_GET = False
ACCOUNT_ADAPTER = 'accounts.adapters.CustomAccountAdapter'
SOCIALACCOUNT_ADAPTER = 'accounts.adapters.CustomSocialAccountAdapter'
SOCIALACCOUNT_LOGIN_ON_GET = False
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_AUTHENTICATION = False
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'
SOCIALACCOUNT_STORE_TOKENS = False
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': (
                exigir('GOOGLE_CLIENT_ID')
                if PRODUCAO
                else config('GOOGLE_CLIENT_ID', default='fictitious-client-id')
            ),
            'secret': (
                exigir('GOOGLE_CLIENT_SECRET')
                if PRODUCAO
                else config(
                    'GOOGLE_CLIENT_SECRET',
                    default='fictitious-client-secret',
                )
            ),
        },
        'SCOPE': ['profile', 'email'],
        'AUTH_PARAMS': {'access_type': 'online'},
    },
}

AXES_FAILURE_LIMIT = 5
AXES_COOLOFF_TIME = timedelta(minutes=15)
AXES_LOCKOUT_PARAMETERS = [['ip_address', 'username']]
AXES_HANDLER = 'axes.handlers.database.AxesDatabaseHandler'
AXES_USERNAME_FORM_FIELD = 'username'
AXES_RESET_ON_SUCCESS = True
AXES_LOCKOUT_TEMPLATE = 'accounts/lockout.html'
AXES_HTTP_RESPONSE_CODE = 403
AXES_IPWARE_PROXY_COUNT = config('AXES_IPWARE_PROXY_COUNT', default=0, cast=int)

TERMOS_VERSAO = config('TERMOS_VERSAO', default='rascunho-2026-11')
RATE_LIMIT_IP = (5, 3600)
RATE_LIMIT_EMAIL = (3, 3600)

AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'
VITRINE_IMAGEM_MAX_BYTES = 2 * 1024 * 1024
VITRINE_IMAGEM_MAX_PIXELS = 16_000_000
VITRINE_IMAGEM_LADO_MAX = 1600
VITRINE_MAX_ITENS = 20

from django.core.exceptions import ImproperlyConfigured


def _validate_storage_backend(*, debug, storage_backend, is_test):
    """
    Guard fail-loud: em produção (DEBUG=False) e fora de testes, o backend
    default de storage NÃO pode ser FileSystemStorage — senão logos e mídias
    são apagados a cada redeploy (disco efêmero do Render/Railway).

    Função pura (sem efeitos colaterais) para permitir teste unitário sem
    reload do módulo de settings.

    Referência: Mini-Sprint 8.1 (guarda de R2 em produção).
    """
    if is_test or debug:
        return
    if storage_backend.endswith('FileSystemStorage'):
        raise ImproperlyConfigured(
            'R2 não configurado em produção. Defina R2_BUCKET_NAME, '
            'R2_ENDPOINT_URL, R2_ACCESS_KEY_ID e R2_SECRET_ACCESS_KEY no '
            '.env antes de rodar com DEBUG=False. '
            'Ver Mini-Sprint 8.1 (guard fail-loud de storage).'
        )


STORAGES = {
    'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
    'staticfiles': {
        'BACKEND': 'whitenoise.storage.CompressedManifestStaticFilesStorage',
    },
}

R2_BUCKET_NAME = exigir('R2_BUCKET_NAME')
R2_ENDPOINT_URL = exigir('R2_ENDPOINT_URL')
R2_ACCESS_KEY_ID = exigir('R2_ACCESS_KEY_ID')
R2_SECRET_ACCESS_KEY = exigir('R2_SECRET_ACCESS_KEY')
if R2_BUCKET_NAME.strip():
    STORAGES['default'] = {
        'BACKEND': 'storages.backends.s3.S3Storage',
        'OPTIONS': {
            'bucket_name': R2_BUCKET_NAME,
            'endpoint_url': R2_ENDPOINT_URL,
            'access_key': R2_ACCESS_KEY_ID,
            'secret_key': R2_SECRET_ACCESS_KEY,
            'region_name': 'auto',
            'signature_version': 's3v4',
            'querystring_auth': True,
            'querystring_expire': 3600,
            'file_overwrite': False,
            'default_acl': None,
        },
    }

_validate_storage_backend(
    debug=DEBUG,
    storage_backend=STORAGES['default']['BACKEND'],
    is_test='test' in sys.argv,
)

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'accounts.CustomUser'
LOGIN_URL = 'accounts:login'
LOGIN_REDIRECT_URL = 'accounts:painel'
LOGOUT_REDIRECT_URL = 'accounts:login'

ADMIN_URL = config('ADMIN_URL', default='admin/')
if not ADMIN_URL.endswith('/') or ADMIN_URL.startswith('/'):
    raise ImproperlyConfigured(
        'ADMIN_URL deve terminar com "/" e não pode começar com "/".'
    )

EMAIL_BACKEND = (
    'accounts.dev_email.ReadableConsoleEmailBackend'
    if DEBUG else 'django.core.mail.backends.smtp.EmailBackend'
)
EMAIL_HOST = config('EMAIL_HOST', default='localhost')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_HOST_USER = (
    exigir('EMAIL_HOST_USER')
    if PRODUCAO
    else config('EMAIL_HOST_USER', default='')
)
EMAIL_HOST_PASSWORD = (
    exigir('EMAIL_HOST_PASSWORD')
    if PRODUCAO
    else config('EMAIL_HOST_PASSWORD', default='')
)
EMAIL_USE_TLS = config('EMAIL_USE_TLS', default=True, cast=bool)
EMAIL_TIMEOUT = config('EMAIL_TIMEOUT', default=10, cast=int)
DEFAULT_FROM_EMAIL = (
    exigir('DEFAULT_FROM_EMAIL')
    if PRODUCAO
    else config('DEFAULT_FROM_EMAIL', default='no-reply@recomecar.local')
)

if PRODUCAO:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_REDIRECT_EXEMPT = [r'^saude/$']
    SECURE_HSTS_SECONDS = config('SECURE_HSTS_SECONDS', default=3600, cast=int)
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'https'
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
            'LOCATION': 'django_cache',
            'OPTIONS': {'MAX_ENTRIES': 5000},
        }
    }
else:
    ACCOUNT_DEFAULT_HTTP_PROTOCOL = 'http'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {'console': {'class': 'logging.StreamHandler'}},
    'loggers': {
        'django': {'handlers': ['console'], 'level': 'INFO'},
        'django.request': {'handlers': ['console'], 'level': 'ERROR', 'propagate': False},
    },
}

if 'test' in sys.argv:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
    PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
    STORAGES = {
        'default': {'BACKEND': 'django.core.files.storage.FileSystemStorage'},
        'staticfiles': {
            'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage',
        },
    }
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }

from csp.constants import NONE, SELF

CONTENT_SECURITY_POLICY = {
    "EXCLUDE_URL_PREFIXES": ["/admin/"],
    "DIRECTIVES": {
        "default-src": [SELF],
        "script-src": [SELF],
        "style-src": [SELF],
        "img-src": [SELF, "data:"],
        "font-src": [SELF],
        "connect-src": [SELF],
        "form-action": [SELF],
        "frame-ancestors": [NONE],
        "base-uri": [SELF],
        "object-src": [NONE],
    },
}
