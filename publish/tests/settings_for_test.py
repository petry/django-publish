import logging
from django.conf.global_settings import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'test.db',
        'USER': '',
        'PASSWORD': '',
    }
}
INSTALLED_APPS = (
    'django.contrib.contenttypes',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.messages',
    'publish',
    'publish.tests.example_app',
    'django_nose',

)

TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
)
MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)


TEST_RUNNER = 'django_nose.NoseTestSuiteRunner'

logging.disable(logging.CRITICAL)

# enable this for coverage (using django test coverage
# http://pypi.python.org/pypi/django-test-coverage )
#TEST_RUNNER = 'django-test-coverage.runner.run_tests'
#COVERAGE_MODULES = ('publish.models', 'publish.admin', 'publish.actions', 'publish.utils', 'publish.signals')
