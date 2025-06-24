from pathlib import Path
import os
from decouple import config  # Muhit o‘zgaruvchilari uchun

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-ids)(@ao7i66-&qt-8x2n9b9pjzxphzgegbu^9ywo*mm=gevqc'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['127.0.0.1', 'localhost']  # Ishlash uchun hostlarni qo‘shdik

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.sites',  # allauth uchun kerak
    'allauth',              # allauth asosiy ilovasi
    'allauth.account',      # account funksiyalari
    'allauth.socialaccount',# ijtimoiy tarmoqlar uchun
    'allauth.socialaccount.providers.google',  # Google OAuth2 uchun
    'users',
    'presentations',
    'payments',
    'feedback',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'allauth.account.middleware.AccountMiddleware',  # allauth uchun qo‘shildi
]

SITE_ID = 1  # allauth uchun kerak, loyiha domenini aniqlaydi

ROOT_URLCONF = 'presentlyai.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / "templates"],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                # allauth uchun context processor qo‘shish shart emas, chunki u avtomatik ishlaydi
            ],
        },
    },
]

WSGI_APPLICATION = 'presentlyai.wsgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
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
    {
        "NAME": "users.validators.CustomPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Statik fayllar uchun sozlamalar
STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'static_collected'  # collectstatic fayllarni bu yerga yig‘adi
STATICFILES_DIRS = [
    BASE_DIR / "static",  # Faqat oddiy statik fayllar qoldi
]

# Media fayllar uchun sozlamalar
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

AUTH_USER_MODEL = 'users.CustomUser'

LOGOUT_REDIRECT_URL = 'index'

# Logging sozlamalari
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "file": {
            "level": "DEBUG",
            "class": "logging.FileHandler",
            "filename": "logs/debug.log",
        },
    },
    "root": {
        "handlers": ["file"],
        "level": "DEBUG",
    },
}

# 📩 Email jo‘natish sozlamalari
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER')  # .env faylidan o‘qish
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD')  # .env faylidan o‘qish
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# Email tasdiqlash havolalari uchun loyiha domeni
SITE_URL = config('SITE_URL', default='http://127.0.0.1:8000')

# Telegram sozlamalari
TELEGRAM_BOT_TOKEN = config('TELEGRAM_BOT_TOKEN')
TELEGRAM_ADMIN_CHAT_ID = config('TELEGRAM_ADMIN_CHAT_ID')

# Google OAuth2 sozlamalari
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

SOCIAL_AUTH_GOOGLE_OAUTH2_KEY = config('SOCIAL_AUTH_GOOGLE_OAUTH2_KEY')
SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET = config('SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET')

LOGIN_REDIRECT_URL = '/'
LOGOUT_REDIRECT_URL = '/'

# OpenAI API kaliti
OPENAI_API_KEY = config('OPENAI_API_KEY')