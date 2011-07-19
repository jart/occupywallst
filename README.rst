.. -*-rst-*-

==============
 OccupyWallSt
==============

:name:        occupywallst
:description: Occupy Wall Street!
:copyright:   © 2011 Justine Tunney
:license:     GNU AGPL v3 or later


Installation
============

This project has been tested on Ubuntu 10.04 LTS and Ubuntu 10.10.

Run these commands in the occupywallst folder::

    sudo ./install_depends.sh
    sudo python setup.py develop
    gunzip <occupywallst/data/init_spatialite-2.3.sql.gz \
        | spatialite occupywallst.db
    occupywallst-dev syncdb
    occupywallst-dev runserver

To use with PostgreSQL::

    sudo apt-get install \
        postgresql-8.4-postgis postgresql-contrib python-psycopg2
    sudo -u postgres -i createuser --superuser $USER
    createdb occupywallst
    createlang plpgsql occupywallst
    if [ -f /usr/share/postgresql/8.4/contrib/postgis-1.5/postgis.sql ]; then
        psql -d occupywallst -f /usr/share/postgresql/8.4/contrib/postgis-1.5/postgis.sql
        psql -d occupywallst -f /usr/share/postgresql/8.4/contrib/postgis-1.5/spatial_ref_sys.sql
    else
        psql -d occupywallst -f /usr/share/postgresql/8.4/contrib/postgis.sql
        psql -d occupywallst -f /usr/share/postgresql/8.4/contrib/spatial_ref_sys.sql
    fi
    occupywallst-dev syncdb
    occupywallst-dev runserver
