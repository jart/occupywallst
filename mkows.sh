#!/bin/bash
#
# OccupyWallSt Setup Script
#
# This script makes it painless to deploy the website into happy
# little self-contained virtualenvs.
#

[ -z $DEST ]           && DEST='.'
[ -z $PROJ ]           && PROJ='ows'
[ -z $DB ]             && DB=$PROJ
[ -z $DOMAIN ]         && DOMAIN='dev.occupywallst.org'
[ -z $RECAPTCHA_PUB ]  && RECAPTCHA_PUB='6Lf32MkSAAAAAMKMBKBqwtjdh2TeYUwVthzgPLRC'
[ -z $RECAPTCHA_PRIV ] && RECAPTCHA_PRIV='6Lf32MkSAAAAAJPNhPJ7moPueeJSfvjfecyG6x1u'
[ -z $REPO ]           && REPO=$(git remote -v 2>/dev/null | grep ^origin | awk '{print $2}' | grep /occupywallst\.git$ | head -n 1)
[ -z $REPO ]           && REPO='git://github.com/jart/occupywallst.git'

cd $DEST

function pg_db_exists {
    psql -Al | grep ^$1\| >/dev/null
    return $?
}

if ! pg_db_exists template_postgis; then
    echo 'Creating template_postgis database...'
    createdb template_postgis || exit 1
    createlang plpgsql template_postgis
    for SQL in $(ls /usr/share/postgresql/*/contrib/{postgis-*,}/{spatial_ref_sys,postgis}.sql 2>/dev/null); do
        psql -q -d template_postgis -f $SQL
    done
fi

# create a virtualenv for our project
virtualenv $PROJ         || exit 1
cd $PROJ                 || exit 1
source bin/activate      || exit 1
git clone $REPO          || exit 1
cd occupywallst          || exit 1
python setup.py develop  || exit 1

# these settings override what's in settings.py *only* for our local install
cat >occupywallst/settings_local.py <<EOF
OWS_SITE_NAME = "$DOMAIN"
OWS_CANONICAL_URL = "http://$DOMAIN"
SESSION_COOKIE_DOMAIN = ".$DOMAIN"
CSRF_COOKIE_DOMAIN = ".$DOMAIN"
SECRET_KEY = "$(head -c 51 /dev/urandom | base64)"
RECAPTCHA_PUBLIC_KEY =  "$RECAPTCHA_PUB"
RECAPTCHA_PRIVATE_KEY = "$RECAPTCHA_PRIV"
DATABASES = {
    "default": {
        "ENGINE": "django.contrib.gis.db.backends.postgis",
        "NAME": "$DB",
    },
}
EOF

# ask postgres to create our new postgis database
createdb $DB
createlang plpgsql $DB
pg_dump template_postgis | psql -q $DB

# ask django to create the schema
occupywallst-dev syncdb --noinput

# load some starting data so the website actually looks normal
occupywallst-dev loaddata verbiage
occupywallst-dev loaddata example_data

# install dependencies for node.js javascript sub-project
cd chat
npm install -d
