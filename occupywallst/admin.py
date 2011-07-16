r"""

    occupywallst.admin
    ~~~~~~~~~~~~~~~~~~

    Django admin gui customization.

"""

from django.contrib import admin, messages
from django.contrib.auth import models as authdb
from django.contrib.gis.admin import OSMGeoAdmin, GeoModelAdmin

from occupywallst import models as db


class GeoAdmin(OSMGeoAdmin):
    # default to philadelphia rather than freakin' africa
    default_lat = 39.95
    default_lon = -75.16
    default_zoom = 2
    map_width = 750
    map_height = 500


class AdminSite(admin.AdminSite):
    def __init__(self, *args, **kwargs):
        admin.AdminSite.__init__(self, *args, **kwargs)
        self.register(authdb.User, GeoAdmin)
        self.register(authdb.Group, GeoAdmin)
        self.register(db.UserInfo, GeoAdmin)
        self.register(db.RideRequest, GeoAdmin)
        self.register(db.Article, GeoAdmin)
        self.register(db.Comment, GeoAdmin)
        self.register(db.Message, GeoAdmin)
        self.register(db.Ride, GeoAdmin)
