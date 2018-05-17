from decouple import config
from unipath import Path
import dj_database_url

BASE_DIR = Path(__file__).parent

SECRET_KEY = config('SECRET_KEY', default='doesntmatter')

DEBUG = config('DEBUG', default=False, cast=bool)

INSTALLED_APPS = [
    # 'django.contrib.admin',
    # 'django.contrib.auth',
    'django.contrib.contenttypes',
    # 'django.contrib.sessions',
    # 'django.contrib.messages',
    # 'django.contrib.staticfiles',

    'buildhub.main',
    'buildhub.ingest',
]


DATABASES = {
    'default': config(
        'DATABASE_URL',
        default='postgresql://localhost/buildhub2',
        cast=dj_database_url.parse
    )
}

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True
