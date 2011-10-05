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

Here's how you get started!

Put this to ``/etc/hosts``::

    127.0.2.1 dev.occupywallst.org
    127.0.2.2 chat.dev.occupywallst.org

Install dependencies::

    sudo ./install_depends.sh

Set up a PostgreSQL database with PostGIS::

    sudo -u postgres -i createuser --superuser root   # make root a pg admin
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

Now install the project and the database schema::

    sudo python setup.py develop
    occupywallst-dev syncdb --noinput
    occupywallst-dev loaddata verbiage
    occupywallst-dev loaddata example_data
    occupywallst-dev runserver 127.0.0.1:9001

Set up nginx.  This is optional (but strongly recommended for
development) and *mandatory* for production::

    sudo apt-get install nginx
    sudo rm /etc/nginx/sites-enabled/default
    sudo cp conf/occupywallst.org.conf /etc/nginx/sites-enabled
    sudo /etc/init.d/nginx restart

Optional: Run the chat server in a second terminal::

    cd chat
    curl http://npmjs.org/install.sh | sudo sh
    npm install -d
    sudo NODE_ENV=development node app.js

Then open this url :) http://dev.occupywallst.org/

There's also a backend for modifying the database and writing
articles.  Go to http://dev.occupywallst.org/admin/ and log in as user
"OccupyWallSt" with the password "anarchy".

If you need to customize Django settings for your local install, do it
inside ``occupywallst/settings_local.py`` and
``chat/settings_local.json`` because git ignores them.


Production Tips
===============

Deploying OccupyWallSt to a production environment takes a bit more
effort.  Please consider the following advice.

Create a user named ows::

    sudo adduser ows
    ssh ows@localhost

Use a virtualenv::

    virtualenv env
    cd env
    source bin/activate
    git clone git://github.com/jart/occupywallst.git
    cd occupywallst
    python setup.py develop
    occupywallst help  <-- this actually runs ../bin/occupywallst

Rather than using Django's "runserver" as the backend HTTP server, I
recommend using gunicorn::

    easy_install gunicorn
    gunicorn_django -b 127.0.0.1:9001 --workers=9 --max-requests=1000 --pid=/tmp/gunicorn-occupywallst.pid occupywallst/settings.py

Use AppArmor to harden security::

    sudo aa-genprof /home/ows/env/bin/gunicorn_django
    sudo aa-complain /home/ows/env/bin/gunicorn_django
    # run gunicorn/occupywallst and do a bunch of stuff on the site
    sudo aa-logprof
    # restart gunicorn/occupywallst and do a bunch of stuff on the site
    sudo aa-logprof
    sudo nano -w /etc/apparmor.d/home.ows.env.bin.gunicorn_django
    sudo aa-enforce /home/ows/env/bin/gunicorn_django

Use pgbouncer to drastically reduce the number of processes PostgreSQL
needs to run.  Now you have more leeway to performance tune
PostgreSQL's settings.  These settings are *very conservative* in
Debian by default, even more so than the default PostgreSQL sources.


Network Topology
================

OccupyWallSt is NOT a simple web application.  It consists of many
network programs all working together and talking to each other.  This
should hopefully give you a better understanding of the system design
in production::

    tcp:occupywallst.org:80       nginx redirects browser to https
    tcp:occupywallst.org:443      nginx load balancing proxy / media server
    tcp:chat.occupywallst.org:80  nginx redirects browser to https
    tcp:chat.occupywallst.org:443 chat/app.js: node.js realtime http stuff
    tcp:chat.occupywallst.org:843 chat/app.js: flashsocket policy server
    udp:127.0.0.1:9010            chat/app.js: notification event subscriber
    tcp:127.0.0.1:9001            gunicorn_django backend http server
    tcp:127.0.0.1:9040            icecast2 mp3 streaming
    tcp:127.0.0.1:8040            freeswitch mod_event_socket
    udp:occupywallst.org:5060     freeswitch sip server
    tcp:occupywallst.org:5060     freeswitch sip server
    tcp:occupywallst.org:5061     freeswitch secure-sip server
    tcp:127.0.0.1:11211           memcached
    tcp:127.0.0.1:5432            postgresql database server
    tcp:127.0.0.1:6432            pgbouncer database connection pooler
