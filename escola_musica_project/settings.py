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
    
    # Django REST Framework
    'rest_framework',
    
    # Autenticação JWT
    'rest_framework_simplejwt',
    
    # CORS para frontend Vercel
    'corsheaders',
    
    # Documentação Swagger/OpenAPI
    'drf_spectacular',
]

# ─── DJANGO-AXES — protecção contra brute force ───────────────────────────────
INSTALLED_APPS += ['axes']

# ─── MIDDLEWARE ───────────────────────────────────────────────────────────────
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'corsheaders.middleware.CorsMiddleware',  # CORS deve vir antes de CommonMiddleware
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',        # proteção CSRF ativa
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'axes.middleware.AxesMiddleware', # Django Axes para proteção contra brute force
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

# ─── BACKENDS DE AUTENTICAÇÃO ────────────────────────────────────────────────
AUTHENTICATION_BACKENDS = [
    # Axes deve vir primeiro
    'axes.backends.AxesStandaloneBackend',

    # teu backend por email
    'escola_musica.auth_backends.EmailBackend',

    # mantém compatibilidade com Django Admin
    'django.contrib.auth.backends.ModelBackend',
]

# Bloqueia após 5 tentativas falhadas
AXES_FAILURE_LIMIT     = 5
# Janela de tempo: 15 minutos
AXES_COOLOFF_TIME      = 0.25   # horas (15 min)
# Bloqueia por IP + username (email)
AXES_LOCKOUT_PARAMETERS = ['ip_address', 'username']
# Não revela detalhes do bloqueio (account enumeration)
AXES_LOCKOUT_TEMPLATE  = None
# Mensagem genérica ao ser bloqueado
AXES_LOCKOUT_CALLABLE  = None
# Axes usa a BD para registar tentativas
AXES_HANDLER           = 'axes.handlers.database.AxesDatabaseHandler'
# reseta contador em login bem sucedido (mais seguro)
AXES_RESET_ON_SUCCESS  = True

# ─── HEADERS DE SEGURANÇA HTTP ────────────────────────────────────────────────
# Ativa em produção (DEBUG=False). Em desenvolvimento local podem ser False.
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'


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
        'contas': {
            'level':     'INFO',
            'class':     'logging.FileHandler',
            'filename':  BASE_DIR / 'logs' / 'contas.log',
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
        'contas_log': {
            'handlers':  ['contas', 'consola'],
            'level':     'INFO',
            'propagate': False,
        },
    },
}

# ─── LOGGING DE AUDITORIA ─────────────────────────────────────────────────────
# Adiciona handler de auditoria ao LOGGING existente
LOGGING['handlers']['auditoria'] = {
    'level':     'INFO',
    'class':     'logging.FileHandler',
    'filename':  BASE_DIR / 'logs' / 'auditoria.log',
    'formatter': 'detalhadо',
}
LOGGING['loggers']['gestao_auditoria'] = {
    'handlers':  ['auditoria', 'consola'],
    'level':     'INFO',
    'propagate': False,
}

SESSION_EXPIRE_AT_BROWSER_CLOSE = True

# ─── DJANGO REST FRAMEWORK ─────────────────────────────────────────────────────
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_PERMISSION_CLASSES': (
        'rest_framework.permissions.IsAuthenticated',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# ─── JWT CONFIGURATION ─────────────────────────────────────────────────────────
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(hours=2),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
}

# ─── CORS CONFIGURATION (Vercel Frontend) ───────────────────────────────────────
CORS_ALLOWED_ORIGINS = config(
    'CORS_ALLOWED_ORIGINS',
    default='http://localhost:3000,http://127.0.0.1:3000',
    cast=lambda x: [s.strip() for s in x.split(',')]
)

CORS_ALLOW_CREDENTIALS = True

# Em produção (Render), permitir todas as origins da Vercel via variável de ambiente
# Exemplo de .env: CORS_ALLOWED_ORIGINS=https://seu-frontend.vercel.app

# ─── SWAGGER/OPENAPI CONFIGURATION ────────────────────────────────────────────
SPECTACULAR_SETTINGS = {
    'TITLE': 'Escola de Música API',
    'DESCRIPTION': 'API REST para gestão de escola de música (alunos, professores, matrículas, aulas)',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
    'SCHEMA_PATH_PREFIX': '/api/v1',
}

