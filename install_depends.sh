#!/bin/bash

if [[ $USER != "root" ]]; then
    echo You need to be root to run me
    exit 1
fi

if [[ ! -f /usr/bin/apt-get ]]; then
    echo You need a debian/ubuntu linux distro
    exit 1
fi

function doit {
    echo $@
    if ! $@; then
        echo "COMMAND FAILED"
        exit 1
    fi
}

echo
echo '----------------------------------------------------------------------'
echo '                  INSTALLING IMPORTANT DEPENDENCIES                   '
echo '----------------------------------------------------------------------'
echo

doit apt-get install --assume-yes \
    build-essential \
    python python-dev python-setuptools python-simplejson python-virtualenv

echo
echo '----------------------------------------------------------------------'
echo '                 INSTALLING GEOGRAPHY DATABASE STUFF                  '
echo '----------------------------------------------------------------------'
echo

if apt-cache search ^postgresql | grep ^postgresql-9.1 >/dev/null 2>&1; then
    # tested on ubuntu 11.10
    doit apt-get install --assume-yes \
        postgresql postgresql-9.1-postgis postgresql-contrib \
        libpq-dev python-psycopg2 gdal-bin proj libgeos-dev \
        libgeoip-dev
else
    # tested on debian 6, ubuntu 10.04, and ubuntu 10.10
    doit apt-get install --assume-yes \
        postgresql-8.4-postgis postgresql-contrib postgresql-contrib-8.4 \
        libpq-dev python-psycopg2 \
        gdal-bin proj libgeos-dev \
        libgeoip-dev
fi

echo
echo '----------------------------------------------------------------------'
echo '           INSTALLING STUFF PROBABLY NEEDED FOR CHAT THING            '
echo '----------------------------------------------------------------------'
echo

doit apt-get install --assume-yes \
    pkg-config memcached libmemcached-dev \
    g++ curl libssl-dev apache2-utils

echo
echo '----------------------------------------------------------------------'
echo '                          INSTALLING NODE.JS                          '
echo '----------------------------------------------------------------------'
echo

apt-get install -q=666 -y nodejs nodejs-dev npm

if ! node -v >/dev/null 2>&1; then
    doit cd /tmp
    doit wget http://nodejs.org/dist/node-v0.4.9.tar.gz
    doit tar -xvzf node-v0.4.9.tar.gz
    doit cd node-v0.4.9
    doit ./configure
    doit make -j4
    doit make install
    doit rm -rf node-v0.4.9.tar.gz node-v0.4.9
else
    echo 'node.js already installed'
fi

if ! npm -v >/dev/null 2>&1; then
    echo 'curl http://npmjs.org/install.sh | sudo sh'
    curl http://npmjs.org/install.sh | sudo sh
else
    echo 'node package manager (npm) already installed'
fi

echo
echo 'All done!'
