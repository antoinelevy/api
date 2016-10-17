"""
Django settings for euskalmoneta project.

Generated by 'django-admin startproject' using Django 1.9.7.

For more information on this file, see
https://docs.djangoproject.com/en/1.9/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.9/ref/settings/
"""

import os

import yaml  # PyYAML

CYCLOS_CONSTANTS = None
with open("/cyclos/cyclos_constants.yml", 'r') as cyclos_stream:
    try:
        CYCLOS_CONSTANTS = yaml.load(cyclos_stream)
    except yaml.YAMLError as exc:
        assert False, exc

DOLIBARR_CONSTANTS = None
with open("/dolibarr/dolibarr_constants.yml", 'r') as dolibarr_stream:
    try:
        DOLIBARR_CONSTANTS = yaml.load(dolibarr_stream)
    except yaml.YAMLError as exc:
        assert False, exc


# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.9/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'kci-=2)4_qh#a3+k#xt!0)_t838t9zjcjpl#&09(&2&kftskr('

# SECURITY WARNING: don't run with debug turned on in production!
# You need to explicitly set DJANGO_DEBUG=True in docker-compose.yml (or environment variable) to have DEBUG on
DEBUG = os.environ.get('DJANGO_DEBUG', False)
if DEBUG and DEBUG in [True, 'true', 'True', 'yes', 'Yes']:
    DEBUG = True
else:
    DEBUG = False

if DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

ALLOWED_HOSTS = ['*']


# Application definition

INSTALLED_APPS = [
    'auth_token',
    'members',

    'bdc_cyclos',
    'bureauxdechange',

    'dolibarr_data',
    'euskalmoneta_data',

    'gestioninterne',

    'corsheaders',
    'raven.contrib.django.raven_compat',
    'rest_framework.authtoken',
    'rest_framework',

    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',

    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.9/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
    }
}


# Password validation
# https://docs.djangoproject.com/en/1.9/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/1.9/topics/i18n/

LANGUAGE_CODE = 'fr-fr'

TIME_ZONE = 'Europe/Paris'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.9/howto/static-files/

STATIC_URL = '/static/'

# Public URLs
API_PUBLIC_URL = os.environ.get('API_PUBLIC_URL')
DOLIBARR_PUBLIC_URL = os.environ.get('DOLIBARR_PUBLIC_URL')
BDC_PUBLIC_URL = os.environ.get('BDC_PUBLIC_URL')
GI_PUBLIC_URL = os.environ.get('GI_PUBLIC_URL')

# APIs URLs
DOLIBARR_URL = 'http://dolibarr-app/api/index.php'
CYCLOS_URL = 'http://cyclos-app:8080/eusko/web-rpc'

# Euskal Moneta internal settings
DATE_COTISATION_ANTICIPEE = '01/11'  # 1er Novembre
if DEBUG:
    MINIMUM_PARRAINAGES_3_POURCENTS = 3  # En production, ce sera bien 30 parrainages et non PAS 3 !
else:
    MINIMUM_PARRAINAGES_3_POURCENTS = 30  # En production, ce sera bien 30 parrainages et non PAS 3 !

if 'https' in BDC_PUBLIC_URL:
    BDC_CORS_URL = BDC_PUBLIC_URL.replace('https://', '')
else:
    BDC_CORS_URL = BDC_PUBLIC_URL.replace('http://', '')

if 'https' in GI_PUBLIC_URL:
    GI_CORS_URL = GI_PUBLIC_URL.replace('https://', '')
else:
    GI_CORS_URL = GI_PUBLIC_URL.replace('http://', '')

# This is needed for Selenium tests to pass (we don't know the URL inside containers)
if DEBUG:
    CORS_ORIGIN_ALLOW_ALL = True
else:
    CORS_ORIGIN_WHITELIST = (
        BDC_CORS_URL,
        GI_CORS_URL,
    )

# Raven + Logging
RAVEN_CONFIG = {
    'dsn': os.environ.get('RAVEN_CONFIG_DSN'),
    'release': 'dev' if DEBUG else 'production',
}

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'root': {
        'level': 'DEBUG',
        'handlers': ['console', 'sentry'],
    },
    'formatters': {
        'simple': {
            'format': '%(asctime)s %(levelname)s %(lineno)d %(name)s %(funcName)s '
                      '%(message)s'
        },
        'verbose': {
            'format': '%(levelname)s %(asctime)s %(module)s '
                      '%(process)d %(thread)d %(message)s'
        },
    },
    'handlers': {
        'sentry': {
            'level': 'WARNING',
            'class': 'raven.contrib.django.raven_compat.handlers.SentryHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose'
        }
    },
    'loggers': {
        'sentry': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'handlers': ['sentry'],
            'propagate': True,
        },
        'all': {
            'level': 'DEBUG' if DEBUG else 'INFO',
            'handlers': ['console', 'sentry'],
            'propagate': True,
        },
    },
}

if DEBUG:
    DEFAULT_RENDERER_CLASSES = (
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    )
else:
    DEFAULT_RENDERER_CLASSES = (
        'rest_framework.renderers.JSONRenderer',
    )

REST_FRAMEWORK = {
    'DEFAULT_RENDERER_CLASSES': DEFAULT_RENDERER_CLASSES,
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication'
    ],
    'DEFAULT_PERMISSION_CLASSES': ['rest_framework.permissions.IsAuthenticated'],
    'DEFAULT_PAGINATION_CLASS': 'pagination.CustomPagination',
    'PAGE_SIZE': 100,
    'TEST_REQUEST_DEFAULT_FORMAT': 'json',
}
