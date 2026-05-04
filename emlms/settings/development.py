from .base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', 'testserver']

# Use local filesystem storage in development
DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'

# Show emails in console during development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Relax email verification for local dev (change to 'mandatory' when testing)
ACCOUNT_EMAIL_VERIFICATION = 'optional'

# django-debug-toolbar
INSTALLED_APPS += ['debug_toolbar']
MIDDLEWARE.insert(0, 'debug_toolbar.middleware.DebugToolbarMiddleware')
INTERNAL_IPS = ['127.0.0.1']

DEBUG_TOOLBAR_CONFIG = {
    'SHOW_TOOLBAR_CALLBACK': lambda request: DEBUG,
}

# Simpler cache in development (no Redis required to start)
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.db'

# Celery: run tasks synchronously in development (no Redis needed to start)
CELERY_TASK_ALWAYS_EAGER = True
CELERY_TASK_EAGER_PROPAGATES = True

# Weaker axes in development
AXES_ENABLED = False

# Disable CSP in development
CSP_DEFAULT_SRC = None
