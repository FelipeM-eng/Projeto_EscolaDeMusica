from pathlib import Path
from decouple import config
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# ─── SEGURANÇA ────────────────────────────────────────────────────────────────
SECRET_KEY = config('SECRET_KEY')
DEBUG = config('DEBUG', default=False, cast=bool)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='localhost').split(',')

# ─── APPS ─────────────────────────────────────────────────────────────────────
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'escola_musica',
]

# ─── MIDDLEWARE ───────────────────────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',        # proteção CSRF ativa
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'escola_musica_project.urls'

# ─── TEMPLATES ────────────────────────────────────────────────────────────────
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'escola_musica_project.wsgi.application'

# ─── BASE DE DADOS ────────────────────────────────────────────────────────────
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME':     config('DB_NAME'),
        'USER':     config('DB_USER'),
        'PASSWORD': config('DB_PASSWORD'),
        'HOST':     config('DB_HOST', default='localhost'),
        'PORT':     config('DB_PORT', default='5432'),
    }
}

# ─── PASSWORDS ───────────────────────────────────────────────────────────────
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# ─── INTERNACIONALIZAÇÃO ──────────────────────────────────────────────────────
LANGUAGE_CODE = 'pt-pt'
TIME_ZONE = 'Europe/Lisbon'
USE_I18N = True
USE_TZ = True

# ─── FICHEIROS ESTÁTICOS (CSS, JS) ───────────────────────────────────────────
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'  # necessário para deploy futuro

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ─── AUTENTICAÇÃO — redireccionamentos ───────────────────────────────────────
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/matriculas/'
LOGOUT_REDIRECT_URL = '/'

# ─── HEADERS DE SEGURANÇA HTTP ────────────────────────────────────────────────
# Ativa em produção (DEBUG=False). Em desenvolvimento local podem ser False.
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# ─── GESTÃO DE SESSÕES (Segurança) ───────────────────────────────────────────

# Sessão expira ao fechar o browser — sem persistência indevida do sessionid
SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# Timeout de inatividade: 15 minutos (em segundos)
# Após este período sem actividade, a sessão é invalidada
SESSION_COOKIE_AGE = 900

# Guarda a sessão a cada pedido para renovar o timeout com actividade real
SESSION_SAVE_EVERY_REQUEST = True

# Impede que o JS aceda ao cookie de sessão (protecção contra XSS)
SESSION_COOKIE_HTTPONLY = True

# Impede envio do cookie em contextos cross-site (protecção contra CSRF)
SESSION_COOKIE_SAMESITE = 'Lax'

# As linhas abaixo exigem HTTPS. Deixa comentadas em desenvolvimento local,
# descomenta quando fizeres deploy num servidor com HTTPS.
# SECURE_SSL_REDIRECT = True
# SESSION_COOKIE_SECURE = True
# CSRF_COOKIE_SECURE = True
# SECURE_HSTS_SECONDS = 3600


# ─── LOGGING — erros internos registados, nunca expostos ao utilizador ────────
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'detalhadо': {
            'format': '[{levelname}] {asctime} {module}: {message}',
            'style': '{',
        },
    },
    'handlers': {
        'ficheiro_erros': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'erros.log',
            'formatter': 'detalhadо',
        },
        'consola': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'detalhadо',
        },
    },
    'loggers': {
        'escola_musica': {
            'handlers': ['ficheiro_erros', 'consola'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django.db.backends': {
            'handlers': ['ficheiro_erros'],
            'level': 'ERROR',
            'propagate': False,
        },
    },
}