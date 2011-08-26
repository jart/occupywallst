
from occupywallst.settings import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG

SESSION_COOKIE_DOMAIN = '.dev.occupywallst.org'
CSRF_COOKIE_DOMAIN = '.dev.occupywallst.org'

TEMPLATE_LOADERS = [
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
]

MIDDLEWARE_CLASSES += ['occupywallst.middleware.PrintException']
MIDDLEWARE_CLASSES += ['occupywallst.middleware.SQLInfoMiddleware']

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'verbose': {
            'format': (GREEN + '%(asctime)s %(levelname)s %(name)s '
                       '%(filename)s:%(lineno)d ' + RESET + '%(message)s'),
        },
        'simple': {
            'format': GREEN + '%(levelname)s ' + RESET + '%(message)s',
        },
    },
    'handlers': {
        'null': {
            'level': 'DEBUG',
            'class': 'django.utils.log.NullHandler',
        },
        'console': {
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        },
    },
    'loggers': {
        'django': {
            'level': 'WARNING',
            'handlers': ['console'],
            'propagate': True,
        },
        'django.request': {
            'level': 'WARNING',
            'handlers': ['console', 'mail_admins'],
            'propagate': False,
        },
        'occupywallst': {
            'level': 'WARNING',
            'handlers': ['console', 'mail_admins'],
            'propagate': False,
        },
    },
}

LOGGING['loggers']['django']['level'] = 'DEBUG'
LOGGING['loggers']['django.request']['level'] = 'DEBUG'
LOGGING['loggers']['occupywallst']['level'] = 'DEBUG'
LOGGING['handlers']['console']['formatter'] = 'verbose'
LOGGING['handlers']['mail_admins'] = {'level': 'DEBUG',
                                      'class': 'django.utils.log.NullHandler'}
