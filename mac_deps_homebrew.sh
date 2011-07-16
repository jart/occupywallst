#!/bin/bash

if [[ $USER != "root" ]]; then
    echo You need to be root to run me
    exit 1
fi

#Cannot assume where brew/fink are

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

echo "Using system python, for shame!"

echo
echo '----------------------------------------------------------------------'
echo '                 INSTALLING GEOGRAPHY DATABASE STUFF                  '
echo '----------------------------------------------------------------------'
echo

doit brew install libspatialite spatialite-tools gdal proj geos sqlite geoip


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
doit /usr/bin/python setup.py install
doit cd ..
doit rm -rf pysqlite-2.6.0/ pysqlite-2.6.0.tar.gz

echo
echo 'All done!'
