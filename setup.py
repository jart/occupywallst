# http://packages.python.org/distribute/setuptools.html
# http://diveintopython3.org/packaging.html
# http://wiki.python.org/moin/CheeseShopTutorial
# http://pypi.python.org/pypi?:action=list_classifiers

from ez_setup import use_setuptools
use_setuptools(version='0.6c11')

import os
from setuptools import setup, find_packages

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

version = __import__('occupywallst').__version__

setup(
    name                 = 'occupywallst',
    version              = version,
    description          = "Occupy Wall Street",
    long_description     = read('README.rst'),
    author               = 'Justine Tunney',
    author_email         = 'jtunney@lobstertech.com',
    license              = 'GNU AGPL v3 or later',
    install_requires     = ['Django==1.3.1', 'python-memcached>=1.40', 'pytz',
                            'markdown', 'twilio', 'django-debug-toolbar',
                            'recaptcha-client', 'gunicorn', 'django-rosetta',
                            'django-imagekit', 'south', 'Whoosh', 'redis'],
    packages             = find_packages(),
    include_package_data = True,
    zip_safe             = False,
    scripts              = ['scripts/' + f for f in os.listdir('scripts')
                            if not f.startswith('.')],
    classifiers = [
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: GNU Affero General Public License v3",
        "Programming Language :: Python",
        "Framework :: Django",
        "Topic :: Communications",
        "Topic :: Internet :: WWW/HTTP",
    ],
)
