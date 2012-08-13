r"""

    occupywallst.settings
    ~~~~~~~~~~~~~~~~~~~~~

    This file is used to configure Django.

"""

import os
import sys
from datetime import timedelta
from os.path import abspath, dirname, join, exists
project_root = dirname(abspath(__file__))

MEDIA_ROOT = join(project_root, 'media')
GEOIP_PATH = join(project_root, 'data')
SHP_PATH = join(project_root, 'data')
WHOOSH_ROOT = join(project_root, 'whoosh')

DEBUG = False
PAYPAL_DEBUG = DEBUG
AUTHNET_DEBUG = DEBUG
TEMPLATE_DEBUG = DEBUG

# please change these values in occupywallst/settings_local.py
OWS_DOMAIN = 'occupywallst.org'
OWS_SITE_NAME = 'OccupyWallSt.org'
OWS_CANONICAL_URL = 'http://occupywallst.org'  # no path or trailing slash
OWS_BLACKHOLE_EMAIL = 'blackhole@occupywallst.org'

OWS_LIMIT_MSG_DAY = 15  # max private messages per day
OWS_LIMIT_THREAD = 60 * 30  # thirty minutes
OWS_LIMIT_COMMENT = 60 * 3  # three minutes
OWS_LIMIT_SIGNUP = 60 * 60 * 30  # three hours
OWS_LIMIT_VOTES = (
    (timedelta(hours=1), 100),  # max 100 votes in an hour
    (timedelta(days=1), 500),  # max 500 votes in a day
)

OWS_MAX_COMMENT_DEPTH = 15
OWS_MAX_PRIVMSG_USER_DAY = 7
OWS_NOTIFY_PUB_ADDR = ('127.0.0.1', 9010)
OWS_KARMA_THRESHOLD = 10
OWS_WORTHLESS_COMMENT_THRESHOLD = -4
OWS_MAX_SUBSCRIBES = 3

OWS_SCRIPTS = ['js/occupywallst/' + fname
               for fname in os.listdir(join(MEDIA_ROOT, 'js/occupywallst'))]
OWS_SCRIPTS_MINIFIED = 'js/occupywallst.min.js'

SECRET_KEY = 'please change me to some wacky random value'
RECAPTCHA_PUBLIC_KEY =  'please change me'
RECAPTCHA_PRIVATE_KEY =  'please change me'
SESSION_COOKIE_DOMAIN = '.occupywallst.org'
CSRF_COOKIE_DOMAIN = '.occupywallst.org'

ADMINS = (
    ('', 'errors@occupywallst.org'),
)

SERVER_EMAIL = 'webmaster@occupywallst.org'
DEFAULT_FROM_EMAIL = 'webmaster@occupywallst.org'

MANAGERS = ADMINS

DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'NAME': 'occupywallst',
    },
}

# store cache entries as json so node.js can read them.  also we don't
# need no goofy key prefixes
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.memcached.MemcachedCache',
        'KEY_PREFIX': project_root,
        'LOCATION': [
            '127.0.0.1:11211',
        ],
    },
    'json': {
        'BACKEND': 'occupywallst.memcachedjson.MemcachedCacheJSON',
        'KEY_FUNCTION': lambda key, key_prefix, version: key,
        'LOCATION': [
            '127.0.0.1:11211',
        ],
    },
}

CACHE_MIDDLEWARE_ANONYMOUS_ONLY = True

BOLD = '\x1b[1m'
GREEN = '\x1b[32m'
RESET = '\x1b[0m'

SITE_ID = 1
USE_I18N = True
USE_L10N = False
USE_THOUSAND_SEPARATOR = True
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_SECURE = False
USE_TZ = True
TIME_ZONE = "US/Eastern"
DEFAULT_CHARSET = 'utf-8'
ROOT_URLCONF = 'occupywallst.urls'
LOGIN_URL = '/login/'
LOGOUT_URL = '/logout/'
LOGIN_REDIRECT_URL = '/'
MEDIA_URL = '/media/'
STATIC_URL = '/media/'
ADMIN_MEDIA_PREFIX = '/media/admin/'
SESSION_ENGINE = "django.contrib.sessions.backends.signed_cookies"
# SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
# SESSION_ENGINE = 'occupywallst.memcachedjson'
USE_X_FORWARDED_HOST = True
ROSETTA_MESSAGES_PER_PAGE = 25
TAGGIT_FORCE_LOWERCASE = True
TAGGIT_STOPWORDS = ['a', 'an', 'and', 'be', 'from', 'of']

gettext_noop = lambda s: s
LANGUAGE_CODE = 'en'
LANGUAGES = (
    ('en', gettext_noop('English')),
    ('es', gettext_noop('Spanish')),
    ('fr', gettext_noop('French')),
    ('de', gettext_noop('German')),
    ('pt', gettext_noop('Portuguese')),
    ('ru', gettext_noop('Russian')),
    ('el', gettext_noop('Greek')),
    ('he', gettext_noop('Hebrew')),
    ('ar', gettext_noop('Arabic')),
    ('hi', gettext_noop('Hindi')),
    ('zh-cn', gettext_noop('Simplified Chinese')),
    ('ja', gettext_noop('Japanese')),
)

TEMPLATE_LOADERS = (
    ('django.template.loaders.cached.Loader', (
        'django.template.loaders.filesystem.Loader',
        'django.template.loaders.app_directories.Loader',
    )),
)

TEMPLATE_CONTEXT_PROCESSORS = [
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.static",
    "django.core.context_processors.request",
    "django.contrib.messages.context_processors.messages",
    "occupywallst.context_processors.goodies",
    "occupywallst.context_processors.notifications",
    "occupywallst.context_processors.verbiage",
]

MIDDLEWARE_CLASSES = [
    'occupywallst.middleware.XForwardedForMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    # 'django.middleware.csrf.CsrfViewMiddleware',
    # 'occupywallst.middleware.CsrfCookieWhenLoggedIn',
    'occupywallst.middleware.NeverCache',
    'occupywallst.middleware.ReCaptchaMiddleware',
]

INSTALLED_APPS = [
    'imagekit',
    'occupywallst',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.admin',
    'django.contrib.gis',
    'rosetta',
    'south',
    'taggit',
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": True,
    "formatters": {
        "verbose": {
            "format": (GREEN + "%(asctime)s %(levelname)s "
                       "[%(filename)s:%(lineno)d] " + RESET + "%(message)s"),
        },
        "simple": {
            "format": GREEN + "%(levelname)s " + RESET + "%(message)s",
        },
        "nocolor": {
            "format": ("%(asctime)s %(levelname)s [%(filename)s:%(lineno)d] "
                       "%(message)s"),
        },
    },
    "handlers": {
        "null": {
            "level": "DEBUG",
            "class": "django.utils.log.NullHandler",
        },
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "mail_admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
            "include_html": True,
        },
        "occupywallst_file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "formatter": "nocolor",
            "filename": join(project_root, "../../log/occupywallst.log"),
        },
        "cdrproc_file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "formatter": "nocolor",
            "filename": join(project_root, "../../log/cdrproc.log"),
        },
    },
    "loggers": {
        "django": {
            "level": "WARNING",
            "handlers": ["console"],
            "propagate": True,
        },
        "django.request": {
            "level": "WARNING",
            "handlers": ["console", "mail_admins"],
            "propagate": False,
        },
        "occupywallst": {
            "level": "WARNING",
            "handlers": ["console", "occupywallst_file", "mail_admins"],
            "propagate": False,
        },
    },
}

try:
    from occupywallst.settings_local import *
except ImportError:
    pass

def minify():
    import subprocess
    minifier = join(project_root, "../chat/minify.js")
    outfile = join(MEDIA_ROOT, OWS_SCRIPTS_MINIFIED)
    infiles = [abspath(join(MEDIA_ROOT, f)) for f in OWS_SCRIPTS]
    if exists(outfile):
        modified = lambda fname: os.stat(fname).st_mtime
        if modified(outfile) > max(modified(infile) for infile in infiles):
            return
        os.unlink(outfile)
    proc = subprocess.Popen([minifier, outfile] + infiles)
    assert proc.wait() == 0, "minifier exited non-zero"
    assert exists(outfile), "minifier didn't produce output"


try:
    minify()
except Exception, exc:
    OWS_SCRIPTS_MINIFIED = ""
    print >>sys.stderr, "javascript minifier failed:", exc
