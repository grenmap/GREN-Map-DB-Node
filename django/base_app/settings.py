"""
Copyright 2022 GRENMap Authors

SPDX-License-Identifier: Apache License 2.0

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

------------------------------------------------------------------------

Synopsis: Django settings for base_app project.

Generated by 'django-admin startproject' using Django 3.0.2.

For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os
import sys
from django.utils.translation import gettext_lazy as _

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
# Base directory of entire project
PROJECT_DIR = os.path.dirname(BASE_DIR)

# Allows for imports relative to base directory to be resolved
sys.path.append(PROJECT_DIR)

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = '*mgw%80+&n%homqva+%q4gk(8$y6-%+d)%mj50r8hc=%epr4iu'
SECRET_KEY = os.environ.get('SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = int(os.environ.get('DEBUG') or 0)

# Sandbox mode
SANDBOX = int(os.environ.get('SANDBOX') or 0)

# Enables test-only views, including REST endpoints
# For now, just follows DEBUG mode
TEST_MODE = DEBUG

# ALLOWED_HOSTS = []
ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS', default='').split(' ')

DJANGO_APPS = [
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.admin',
]

DEPENDENCY_APPS = [
    # TODO: #138 Cachalot breaks multiple polling
    # 'cachalot',
    'django_q',
    'drf_spectacular',
    'nested_inline',
    'rest_framework',
]

GRENMAP_APPS = [
    'base_app',
    'collation',
    'fim',
    'grenml_export',
    'grenml_import',
    'network_topology',
    'published_network_data',
    'visualization',
]

# Add polling app if not in sandbox mode.
if not SANDBOX:
    GRENMAP_APPS += ['polling']

# Custom apps should appear before django.contrib.admin
INSTALLED_APPS = GRENMAP_APPS + DJANGO_APPS + DEPENDENCY_APPS

# List of apps which need tokens
TOKEN_TYPES = [
    ('grenml_import', _('Import')),
    ('grenml_export', _('Polling')),
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'csp.middleware.CSPMiddleware',
]

ROOT_URLCONF = 'base_app.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'templates'),
            os.path.join(BASE_DIR, 'collation', 'templates')
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'base_app.context_processors.build_attributes',
            ],
        },
    },
]

WSGI_APPLICATION = 'base_app.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': os.environ.get('SQL_ENGINE', 'django.db.backends.sqlite3'),
        'HOST': os.environ.get('SQL_HOST', 'localhost'),
        'PORT': os.environ.get('SQL_PORT', '5432'),
        'NAME': os.environ.get('POSTGRES_DB', os.path.join(BASE_DIR, 'db.sqlite3')),
        'USER': os.environ.get('POSTGRES_USER', 'user'),
        'PASSWORD': os.environ.get('POSTGRES_PASSWORD', 'password'),
    }
}

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.0/topics/i18n/

# Supported language list
LANG_EN = 'en'
LANG_FR = 'fr'
LANG_ES = 'es'
LANG_PT = 'pt'
LANGUAGES = [
    (LANG_FR, _('French')),
    (LANG_EN, _('English')),
    (LANG_ES, _('Spanish')),
    (LANG_PT, _('Portuguese')),
]

# Default language
LANGUAGE_CODE = LANG_EN

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/
# STATIC_URL = '/static/'
STATIC_URL = '/staticfiles/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    '/home/grenmapadmin/static',
]

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')
MEDIA_URL = '/media/'

# CSP header configuration
CSP_INCLUDE_NONCE_IN = [
    'script-src',

    # Once AOT for gren-map-visualization is in place,
    # uncomment this and remove 'unsafe-inline' in CSP_STYLE_SRC.
    # 'style-src',
]
CSP_DEFAULT_SRC = ["'self'"]
CSP_STYLE_SRC = ["'self'", "'unsafe-inline'"]
CSP_SCRIPT_SRC = [
    "'self'",
    # CSP blocks all the js files under staticfiles/admin/
    # "'strict-dynamic'",
]
CSP_FONT_SRC = ["'self'", 'https://fonts.gstatic.com/s/']
CSP_OBJECT_SRC = ["'none'"]
CSP_IMG_SRC = [
    "'self' data:",
    'https://tiles.stadiamaps.com/tiles/',
    'https://*.tile.openstreetmap.org/',
]
CSP_BASE_URI = ["'self'"]

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'timestamped': {
            'format': (
                '{asctime} [{process}] [{levelname}] :: '
                '{name} :: {message}'
            ),
            'datefmt': '[%Y-%m-%d %H:%M:%S %z]',
            'style': '{',
        },
        'importing': {
            'format': (
                '[{process}] [{levelname}] :: '
                'importing :: {message}'
            ),
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'timestamped'
        },
        'importing': {
            'class': 'logging.StreamHandler',
            'formatter': 'importing'
        },
    },
    'loggers': {
        '': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'django-q': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'DEBUG'),
            'propagate': False,
        },
        'collation': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'collation.rule_types': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'grenml_import': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'importing': {
            'handlers': ['importing'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'grenml_export': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'exporting': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
    },
}

CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = 300
CACHE_MIDDLEWARE_KEY_PREFIX = ''

# Caching functionality to speed up common requests
REDIS_HOST = os.environ.get('REDIS_HOST')
if REDIS_HOST is not None:
    CACHES = {
        'default': {
            'TIMEOUT': None,
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_HOST,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'MAX_ENTRIES': 1000
            }
        }
    }

Q_CLUSTER = {
    'name': 'gren_cluster',
    'workers': 8,
    'recycle': 500,
    'log_level': 'DEBUG',

    # https://django-q.readthedocs.io/en/latest/brokers.html
    # The Redis broker does not support message receipts.This means
    # that in case of worker timeouts, tasks that were being executed
    # get lost. Therefore, configure a large value for the timeout.
    'timeout': int(os.environ.get('DJANGO_Q_TIMEOUT', 60 * 60)),
    'retry': 60 * 90,

    'compress': True,
    'save_limit': 250,
    'queue_limit': 500,
    'cpu_affinity': 1,
    'label': 'Django Q',

    # This setting is used to prevent missing polling jobs
    'catch_up': True,

    'redis': {
        'host': 'redis',
        'port': 6379,
        'db': 0,
    },
}

# Default timeout value for http request
REQUEST_TIMEOUT = 300

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Cache the network topology for faster graphql queries
CACHALOT_ONLY_CACHABLE_APPS = frozenset([
    'network_topology'
])

# Required by Django 3.2
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# This is related to the /api-schema endpoint currently defined in
# base_app.urls. The endpoint responds with an OpenAPI schema file.
REST_FRAMEWORK = {
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# Reference:
# https://drf-spectacular.readthedocs.io/en/latest/settings.html
SPECTACULAR_SETTINGS = {
    'TITLE': 'GRENMap public API',
    'DESCRIPTION': 'Global Map of Research and Education Networks',
    'VERSION': '0.1.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'SERVERS': [{
        'url': '',
        'description': 'GRENMap server',
    }],
    'APPEND_COMPONENTS': {
        'securitySchemes': {
            'import token': {
                'type': 'http',
                'scheme': 'bearer',
            },
            'polling token': {
                'type': 'http',
                'scheme': 'bearer',
            }
        }
    },
    'DEFAULT_GENERATOR_CLASS': 'base_app.schema.GRENMapSchemaGenerator',
}


def make_locale_paths():
    """
    Computes a value for LOCALE_PATHS, which Django uses to find
    locale files.
    """
    result = [os.path.join(BASE_DIR, app, 'locale') for app in GRENMAP_APPS]

    # TODO use DEPENDENCY_APPS to put other dependency apps
    # in LOCALE_PATHS

    # add django_q
    django_q_locale_path = os.environ.get('DJANGO_Q_LOCALE_PATH')
    if django_q_locale_path is not None:
        result.append(django_q_locale_path)

    return result


LOCALE_PATHS = make_locale_paths()
