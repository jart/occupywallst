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

This project has been tested on Ubuntu 10.04 LTS and Ubuntu 10.10.  If
you're not using Ubuntu >= 10.04 or a recent Debian then spare your
sanity and set up a virtual machine.

Here's how you get started.

Put this to ``/etc/hosts``::

    127.0.2.1 dev.occupywallst.org
    127.0.2.2 chat.dev.occupywallst.org

Install dependencies::

    sudo ./install_depends.sh

Set up a PostgreSQL database with PostGIS::

    sudo -u postgres -i createuser --superuser root  # make root a pg admin
    sudo -u postgres -i createuser --superuser $USER  # make you a pg admin
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

Run the mini django http server::

    occupywallst-dev runserver 127.0.0.1:9001

Set up nginx::

    sudo apt-get install nginx
    sudo rm /etc/nginx/sites-enabled/default
    sudo cp conf/occupywallst.org.conf /etc/nginx/sites-enabled
    sudo /etc/init.d/nginx restart

Run the chat server in a second terminal::

    cd chat
    curl http://npmjs.org/install.sh | sudo sh
    npm install -d
    sudo NODE_ENV=development node app.js

Then open this url :) http://dev.occupywallst.org/

If you need to customize Django settings for your local install, make
a file named ``occupywallst/settings_local.py`` and do it there.
