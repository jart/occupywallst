r"""

    occupywallst.settings
    ~~~~~~~~~~~~~~~~~~~~~

    This file is used to configure Django.

"""

import re
import os
import sys
from os.path import abspath, dirname, join, exists
project_root = dirname(abspath(__file__))

MEDIA_ROOT = join(project_root, 'media')
GEOIP_PATH = join(project_root, 'data')
SHP_PATH = join(project_root, 'data')

DEBUG = False
PAYPAL_DEBUG = DEBUG
AUTHNET_DEBUG = DEBUG
TEMPLATE_DEBUG = DEBUG

OWS_POST_LIMIT_THREAD = 60 * 5  # five minutes
OWS_POST_LIMIT_COMMENT = 30  # 30 seconds
OWS_CANONICAL_URL = 'https://occupywallst.org'  # no path or trailing slash
OWS_NOTIFY_PUB_ADDR = ('127.0.0.1', 9010)

OWS_SCRIPTS = ['js/occupywallst/' + fname
               for fname in os.listdir(join(MEDIA_ROOT, 'js/occupywallst'))]
OWS_SCRIPTS_MINIFIED = 'js/occupywallst.min.js'

ADMINS = (
    ('', 'errors@occupywallst.org'),
)
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
        'BACKEND': 'occupywallst.memcachedjson.MemcachedCacheJSON',
        'KEY_FUNCTION': lambda key, key_prefix, version: key,
        'LOCATION': [
            '127.0.0.1:11211',
        ],
    }
}

BOLD = '\x1b[1m'
GREEN = '\x1b[32m'
RESET = '\x1b[0m'

SITE_ID = 1
USE_I18N = True
USE_L10N = False
USE_THOUSAND_SEPARATOR = True
SESSION_COOKIE_SECURE = False
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_DOMAIN = '.occupywallst.org'
CSRF_COOKIE_DOMAIN = '.occupywallst.org'
CSRF_COOKIE_SECURE = False
TIME_ZONE = 'UTC'
LANGUAGE_CODE = 'en-us'
DEFAULT_CHARSET = 'utf-8'
ROOT_URLCONF = 'occupywallst.urls'
LOGIN_URL = '/login/'
LOGOUT_URL = '/logout/'
LOGIN_REDIRECT_URL = '/'
MEDIA_URL = '/media/'
ADMIN_MEDIA_PREFIX = '/media/admin/'
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'

# change me in production
SECRET_KEY = 'oek(taazh36*h939oau#$%()dhueha39h(3zhc3##ev_jpfyd2'

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
]

MIDDLEWARE_CLASSES = [
    'django.middleware.common.CommonMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'occupywallst.middleware.NeverCache',
]

INSTALLED_APPS = [
    'occupywallst',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.admin',
    'django.contrib.gis',
]

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
