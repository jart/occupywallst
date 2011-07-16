r"""

    occupywallst.api
    ~~~~~~~~~~~~~~~~

    Ajax data providers.

    They just return plain old python data and have nothing to do with
    the HTTP request/response logic.  To make these functions return
    something like JSON we use middleware decorators (such as
    ``api_view()``) which are specified in the ``urls.py`` file.

"""

from django.contrib import auth
from django.contrib.gis.geos import Polygon
from django.contrib.auth import forms as authforms

from occupywallst import utils, models as db


def attendees(bounds, **kwargs):
    """Find all people going who live within visible map area.
    """
    if bounds:
        bounds = Polygon.from_bbox([float(s) for s in bounds.split(',')])
        qset = db.UserInfo.objects.filter(position__isnull=False,
                                          position__within=bounds)
    else:
        qset = db.UserInfo.objects.filter(position__isnull=False)
    for userinfo in qset[:100]:
        yield {'id': userinfo.user.id,
               'username': userinfo.user.username,
               'position': [userinfo.position.x,
                            userinfo.position.y]}


def user(username, **kwargs):
    """Get information about a user
    """
    user = db.User.objects.get(username=username)
    yield {'id': user.id,
           'username': user.username,
           'info': user.userinfo.info,
           'need_ride': user.userinfo.need_ride,
           'location': [user.userinfo.position.x,
                        user.userinfo.position.y]}
