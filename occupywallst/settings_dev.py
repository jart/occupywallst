import sys
from occupywallst.settings import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG

TEMPLATE_LOADERS = [
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
]

INTERNAL_IPS = [
    '127.0.0.1',
]

MIDDLEWARE_CLASSES += ["debug_toolbar.middleware.DebugToolbarMiddleware"]
INSTALLED_APPS += ["debug_toolbar"]
DEBUG_TOOLBAR_CONFIG = {
    'INTERCEPT_REDIRECTS': False,
}

LOGGING["loggers"]["django"]["level"] = "DEBUG"
LOGGING["loggers"]["django.request"]["level"] = "DEBUG"
LOGGING["loggers"]["occupywallst"]["level"] = "DEBUG"
LOGGING["handlers"]["console"]["formatter"] = "verbose"
LOGGING["handlers"]["mail_admins"] = {"level": "DEBUG",
                                      "class": "django.utils.log.NullHandler"}

try:
    from occupywallst.settings_dev_local import *
except ImportError:
    pass
