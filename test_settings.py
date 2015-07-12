from project.settings import *

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': 'unicore_mc.db',
        'USER': '',
        'PASSWORD': '',
        'HOST': '',
        'PORT': '',
    }
}

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
    }
}

DEBUG = True
CELERY_ALWAYS_EAGER = True

UNICORE_CMS_INSTALL_DIR = abspath('.test_config_dir', 'unicore-cms-django')
UNICORE_CMS_PYTHON_VENV = '/path/to/bin/python'
UNICORE_CONFIGS_INSTALL_DIR = '/path/to/unicore-configs'

REPO_WORKSPACE = '.test_repo_dir'
FRONTEND_REPO_PATH = abspath(REPO_WORKSPACE, 'frontend')
CMS_REPO_PATH = abspath(REPO_WORKSPACE, 'cms')

CONFIG_WORKSPACE = '.test_config_dir'
CONFIGS_REPO_PATH = abspath('.test_config_repo_dir')
NGINX_CONFIGS_PATH = abspath(CONFIGS_REPO_PATH, 'nginx')
SPRINGBOARD_SETTINGS_OUTPUT_PATH = abspath(
    CONFIGS_REPO_PATH, 'springboard_settings')
FRONTEND_SETTINGS_OUTPUT_PATH = abspath(
    CONFIGS_REPO_PATH, 'frontend_settings')
CMS_SETTINGS_OUTPUT_PATH = abspath(CONFIG_WORKSPACE, 'cms_settings')

FRONTEND_SOCKETS_PATH = abspath('.test_sockets_dir', 'frontend_sockets')
CMS_SOCKETS_PATH = abspath('.test_sockets_dir', 'cms_sockets')

RAVEN_DSN_FRONTEND_QA = 'raven-qa'
RAVEN_DSN_FRONTEND_PROD = 'raven-prod'

RAVEN_DSN_CMS_QA = 'raven-cms-qa'
RAVEN_DSN_CMS_PROD = 'raven-cms-prod'

ELASTICSEARCH_HOST = 'http://localhost:9200'
UNICORE_DISTRIBUTE_HOST = 'http://testserver:6543'
MESOS_MARATHON_HOST = 'http://testserver:8080'

THUMBOR_SECURITY_KEY = 'some-key'

HUBCLIENT_SETTINGS = {
    'host': 'http://testserver:8888',
    'app_id': '',
    'app_key': '',
    'redirect_to_https': False,
}
