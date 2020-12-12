"""
Django settings for school_diary project.
Generated by 'django-admin startproject' using Django 3.0.2.
For more information on this file, see
https://docs.djangoproject.com/en/3.0/topics/settings/
For the full list of settings and their values, see
https://docs.djangoproject.com/en/3.0/ref/settings/
"""

import os
from configparser import RawConfigParser

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
config = RawConfigParser()
thisfolder = os.path.dirname(os.path.abspath(__file__))
initfile = os.path.join(thisfolder, 'settings.ini')
config.read(initfile)
SECRET_KEY = config.get('Settings', 'secret_key_a')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = (config.get("Settings", "debug") == "True")

ALLOWED_HOSTS = ['.diary56.ru', '64.227.75.146']

if DEBUG:
    ALLOWED_HOSTS.extend(['127.0.0.1', 'localhost'])

# Application definition

INSTALLED_APPS = [
    # Django
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # Apps
    'timetable.apps.TimetableConfig',
    'minimum.apps.MinimumConfig',
    'diary.apps.DiaryConfig',
    'news.apps.NewsConfig',
    'admin_panel',
    'pages',
    'accounts',
    'grades',
    'api',
    # Third party
    'crispy_forms',  # "Bootstrapped" forms
    'rest_framework',  # Working with API
    'rest_framework.authtoken',  # Token authentication for REST API
    'django_cleanup',  # Deleting unused files in storage
    'debug_toolbar',  # Displaying debug info
    'django_extensions',  # Advances manage.py functions
    'django_filters',  # Filtering support for API
    'widget_tweaks',
    # TODO: Deprecate crispy forms
]

CRISPY_TEMPLATE_PACK = 'bootstrap4'
"""Lets Django to style created forms with bootstrap 4"""

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    'django.middleware.common.BrokenLinkEmailsMiddleware',
]

ROOT_URLCONF = 'school_diary.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': ['templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'libraries': {'templateLibs': 'templateLibs'},
        },
    },
]

# CUSTOM USER MODEL SUPPORT
AUTH_USER_MODEL = 'diary.Users'

WSGI_APPLICATION = 'school_diary.wsgi.application'

if not DEBUG:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            'NAME': config.get("DataBase", 'name'),
            'USER': config.get("DataBase", 'user'),
            'PASSWORD': config.get('DataBase', 'password'),
            'HOST': 'localhost',
            'PORT': '',
            'ATOMIC_REQUESTS': True,
        }
    }
else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(BASE_DIR, 'db.sqlite3'),
            'ATOMIC_REQUESTS': True,
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

INTERNAL_IPS = [
    # ...
    '127.0.0.1',
    # ...
]

# Internationalization
# https://docs.djangoproject.com/en/3.0/topics/i18n/

LANGUAGE_CODE = 'ru'

TIME_ZONE = 'Europe/Moscow'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = '/static/'
if not DEBUG:
    STATIC_ROOT = os.path.join(BASE_DIR, 'static/')
else:
    STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]
MEDIA_URL = '/media/'

MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

AUTH_USER_MODEL = 'diary.Users'
ACCOUNT_AUTHENTICATION_METHOD = 'email'


# SMTP CONFIGURATIONS
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.yandex.ru'
EMAIL_PORT = 465
EMAIL_USE_TLS = False
EMAIL_USE_SSL = True
EMAIL_HOST_USER = config.get("Email", 'user')
EMAIL_HOST_PASSWORD = config.get("Email", 'password')
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# Administrators list and their emails to get Django reports.
ADMINS = [
    ('Maxim', 'alantheknight2@gmail.com'),
    ('IdeaSoft', 'ideasoft-spb@yandex.ru'),
    ('Pasha', 'pashs.ba@gmail.com')
]

if not DEBUG:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'file': {
                'level': 'DEBUG',
                'class': 'logging.FileHandler',
                'filename': '/home/alan/diary/logs/warning.log',
            },
        },
        'loggers': {
            'django': {
                'handlers': ['file'],
                'level': 'DEBUG',
                'propagate': True,
            },
        },
    }

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': ['django_filters.rest_framework.DjangoFilterBackend'],
    'DEFAULT_AUTHENTICATION_CLASSES': [],
}
