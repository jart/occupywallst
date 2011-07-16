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
    python python-dev python-setuptools

echo
echo '----------------------------------------------------------------------'
echo '                 INSTALLING GEOGRAPHY DATABASE STUFF                  '
echo '----------------------------------------------------------------------'
echo

doit apt-get install --assume-yes \
    libsqlite3-dev libspatialite-dev spatialite-bin \
    gdal-bin proj libgeos-dev \
    libgeoip-dev

echo
echo '----------------------------------------------------------------------'
echo '        INSTALLING PYSQLITE DATABASE DRIVER WITH BONUS FEATURE        '
echo '----------------------------------------------------------------------'
echo

doit cd /tmp
doit wget http://pysqlite.googlecode.com/files/pysqlite-2.6.0.tar.gz
doit tar -xvzf pysqlite-2.6.0.tar.gz
doit cd pysqlite-2.6.0
doit sed -i -e 's/define=SQLITE/#define=SQLITE/' setup.cfg
doit python setup.py install
doit cd ..
doit rm -rf pysqlite-2.6.0/ pysqlite-2.6.0.tar.gz

echo
echo 'All done!'
