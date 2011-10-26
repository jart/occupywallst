r"""

    occupywallst.context_processors
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tell Django to define certain template variables by default.

"""

from django.conf import settings
from occupywallst import models as db
from django.utils.safestring import mark_safe
from django.core.exceptions import ObjectDoesNotExist


class VerbiageGetter(object):
    def __init__(self, request):
        self.request = request

    def __getitem__(self, key):
        try:
            return mark_safe(db.Verbiage.get(key, self.request.LANGUAGE_CODE))
        except ObjectDoesNotExist:
            return ''


def verbiage(request):
    return {'verbiage': VerbiageGetter(request)}


def goodies(request):
    return {'OWS_CANONICAL_URL': settings.OWS_CANONICAL_URL,
            'OWS_SCRIPTS': settings.OWS_SCRIPTS,
            'OWS_SCRIPTS_MINIFIED': settings.OWS_SCRIPTS_MINIFIED,
            'OWS_SITE_NAME': settings.OWS_SITE_NAME,
            'DEBUG': settings.DEBUG,
            'base': 'occupywallst/base.html'}


def notifications(request):
    if request.user.is_authenticated():
        qset = (request.user.notification_set
                .filter(is_read=False)
                .order_by('published'))
        return {'notifications': qset}
    else:
        return {}
