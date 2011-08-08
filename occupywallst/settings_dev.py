
from occupywallst.settings import *

DEBUG = True
TEMPLATE_DEBUG = DEBUG

SESSION_COOKIE_DOMAIN = '.dev.occupywallst.org'
CSRF_COOKIE_DOMAIN = '.dev.occupywallst.org'

MIDDLEWARE_CLASSES += ['occupywallst.middleware.PrintException']

LOGGING['loggers']['django']['level'] = 'DEBUG'
LOGGING['loggers']['django.request']['level'] = 'DEBUG'
LOGGING['loggers']['occupywallst']['level'] = 'DEBUG'
LOGGING['handlers']['console']['formatter'] = 'verbose'
LOGGING['handlers']['mail_admins'] = {'level': 'DEBUG',
                                      'class': 'django.utils.log.NullHandler'}
