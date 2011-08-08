r"""

    occupywallst.context_processors
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tell Django to define certain template variables by default.

"""

from django.conf import settings

from occupywallst import models as db


def goodies(request):
    if 'content_only' in request.REQUEST:
        base = 'occupywallst/base_content_only.html'
    else:
        base = 'occupywallst/base.html'
    return {'OWS_CANONICAL_URL': settings.OWS_CANONICAL_URL,
            'DEBUG': settings.DEBUG,
            'base': base}


def notifications(request):
    if request.user.is_authenticated():
        qset = request.user.notification_set.filter(is_read=False)
        return {'notifications': qset}
    else:
        return {}
