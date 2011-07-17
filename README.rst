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
