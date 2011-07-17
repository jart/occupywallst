r"""

    occupywallst.api
    ~~~~~~~~~~~~~~~~

    Ajax data providers.

    They just return plain old python data and have nothing to do with
    the HTTP request/response logic.  To make these functions return
    something like JSON we use middleware decorators (such as
    ``api_view()``) which are specified in the ``urls.py`` file.

"""

from django.contrib.gis.geos import Polygon

from occupywallst import models as db


def str_to_bbox(val):
    swlat, swlng, nwlat, nwlng = [float(s) for s in val.split(',')]
    return Polygon.from_bbox([swlng, swlat, nwlng, nwlat])


def attendees(bounds, **kwargs):
    """Find all people going who live within visible map area.
    """
    if bounds:
        bbox = str_to_bbox(bounds)
        qset = db.UserInfo.objects.filter(position__isnull=False,
                                          position__within=bbox)
    else:
        qset = db.UserInfo.objects.filter(position__isnull=False)
    for userinfo in qset[:100]:
        yield {'id': userinfo.user.id,
               'username': userinfo.user.username,
               'position': userinfo.position_latlng}


def user(username, **kwargs):
    """Get information about a user
    """
    user = db.User.objects.get(username=username)
    yield {'id': user.id,
           'username': user.username,
           'info': user.userinfo.info,
           'need_ride': user.userinfo.need_ride,
           'location': user.userinfo.position_latlng}
