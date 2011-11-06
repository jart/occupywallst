.. -*-rst-*-

==============
 OccupyWallSt
==============

:name:        occupywallst
:description: Occupy Wall Street!
:copyright:   © 2011 Justine Tunney, et al.
:license:     GNU AGPL v3 or later


Installation
============

This project has been tested on Debian 6 (recommended), Ubuntu 10.04,
10.10, and 11.10.  If you're not using one of these distros then spare
your sanity and set up a virtual machine.

Read this if you're using PostgreSQL 9.1:
http://psycopg.lighthouseapp.com/projects/62710-psycopg/tickets/69

Right now you can ignore most of the chat/real-time related stuff
because I couldn't figure out how to make node.js/socket.io *not* leak
a ridiculous amount of memory.  When the website was getting only
25,000 visitors a day it would leak about 300 megs of memory an hour.
I'm pretty confident this wasn't my fault because most of those
requests were being plugged into about 10 lines of code I wrote in the
notifications section in ``chat/app.js``.

Anyway here's how you get started!

Perform some basic system changes::

    sudo -u postgres -i createuser --superuser root   # make root a pg admin
    sudo -u postgres -i createuser --superuser $USER  # make you a pg admin
    sudo chmod go+rwt /opt  # let all users create files in /opt

Define pseudo hostnames by putting this in ``/etc/hosts``::

    127.0.2.1 dev.occupywallst.org
    127.0.2.2 chat.dev.occupywallst.org

Install dependencies::

    wget -qO- https://raw.github.com/jart/occupywallst/master/install_depends.sh | bash

Now we're going to run the install script to create a virtualenv,
install the project, create the database, load the database content,
and create a local settings file::

    export DEST='/opt'
    export REPO='git@github.com:$USER/occupywallst.git'  # did you make your github fork yet?
    wget -qO- https://raw.github.com/jart/occupywallst/master/mkows.sh | bash
    cd /opt/occupywallst/occupywallst
    source ../bin/activate

Now we'll setup nginx as our webserver::

    sudo apt-get install nginx
    sudo rm /etc/nginx/sites-enabled/default
    sudo cp conf/occupywallst.org.conf /etc/nginx/sites-available/
    pushd /etc/nginx/sites-enabled/; sudo ln -sf ../sites-available/occupywallst.org.conf; popd
    sudo /etc/init.d/nginx restart

Which will forward requests to our internally running webserver::

    occupywallst runserver 9000

Then open this url :) http://dev.occupywallst.org/

There's also a backend for modifying the database and writing
articles.  Go to http://dev.occupywallst.org/admin/ and log in as user
"OccupyWallSt" with the password "anarchy".

If you need to customize Django settings for your local install, do it
inside ``occupywallst/settings_local.py``.


Testing
=======

To run the regression tests::

    occupywallst test occupywallst


Production Tips
===============

Rather than using Django's "runserver" as the backend HTTP server, I
recommend using gunicorn::

    /opt/ows/bin/gunicorn_django -b 127.0.0.1:9000 --workers=9 --max-requests=1000 --pid=/tmp/gunicorn-occupywallst.pid occupywallst/settings.py

AppArmor allows you to write mandatory access controls that will
reduce the potential damage of future security exploits::

    sudo aa-genprof /opt/ows/bin/gunicorn_django
    sudo aa-complain /opt/ows/bin/gunicorn_django
    # run gunicorn/occupywallst and do a bunch of stuff on the site
    sudo aa-logprof
    # restart gunicorn/occupywallst and do a bunch of stuff on the site
    sudo aa-logprof
    sudo nano -w /etc/apparmor.d/opt.ows.bin.gunicorn_django
    sudo aa-enforce /opt/ows/bin/gunicorn_django

pgbouncer should be used to drastically reduce the number of processes
postgres needs to run.  Running fewer postgresql processes also means
you can configure postgres to use lots of memory for better
performance.

These fancy indexes will optimize the performance of certain slow
queries::

    -- optimize: recent comments on forum page
    create index occupywallst_comment_published
      on occupywallst_comment (published desc)
      where (is_removed = false and is_deleted = false);

    -- optimize: forum thread list
    create index occupywallst_article_killed
      on occupywallst_article (killed desc)
      where (is_visible = true and is_deleted = false);


Network Topology
================

When you run the kitchen sink, there are many network programs all
working together and talking to each other.  This should hopefully
give you a better understanding of the system design in production::

    tcp:occupywallst.org:80       nginx redirects browser to https
    tcp:occupywallst.org:443      nginx load balancing proxy / media server
    tcp:chat.occupywallst.org:80  nginx redirects browser to https
    tcp:chat.occupywallst.org:443 chat/app.js: node.js realtime http stuff
    tcp:chat.occupywallst.org:843 chat/app.js: flashsocket policy server
    udp:127.0.0.1:9010            chat/app.js: notification event subscriber
    tcp:127.0.0.1:9000            gunicorn_django backend http server
    tcp:127.0.0.1:9040            icecast2 mp3 streaming
    tcp:127.0.0.1:8040            freeswitch mod_event_socket
    udp:occupywallst.org:5060     freeswitch sip server
    tcp:occupywallst.org:5060     freeswitch sip server
    tcp:occupywallst.org:5061     freeswitch secure-sip server
    tcp:127.0.0.1:11211           memcached
    tcp:127.0.0.1:5432            postgresql database server
    tcp:127.0.0.1:6432            pgbouncer database connection pooler

Testing
=======

Getting testing to run requires some work, because of the GIS
business.  Notes on it here::

    https://docs.djangoproject.com/en/dev/ref/contrib/gis/install/#spatialdb-template

Do the following::

    POSTGIS_SQL_PATH=`pg_config --sharedir`/contrib
    createdb -E UTF8 template_postgis
    createlang -d template_postgis plpgsql
    # Allows non-superusers the ability to create from this template
    psql -d postgres -c "UPDATE pg_database SET datistemplate='true' WHERE datname='template_postgis';"
    # Loading the PostGIS SQL routines
    psql -d template_postgis -f $POSTGIS_SQL_PATH/postgis.sql
    psql -d template_postgis -f $POSTGIS_SQL_PATH/spatial_ref_sys.sql
    # Enabling users to alter spatial tables.
    psql -d template_postgis -c "GRANT ALL ON geometry_columns TO PUBLIC;"
    #psql -d template_postgis -c "GRANT ALL ON geography_columns TO PUBLIC;"
    psql -d template_postgis -c "GRANT ALL ON spatial_ref_sys TO PUBLIC;"

Then you should be able to run tests as follows (note that this must be run from the project dir)::

    occupywallst-dev test
    occupywallst-dev test occupywallst  # faster
