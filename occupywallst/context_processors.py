r"""

    occupywallst.context_processors
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tell Django to define certain template variables by default.

"""

from django.conf import settings


def goodies(request):
    if 'content_only' in request.REQUEST:
        base = 'occupywallst/base_content_only.html'
    else:
        base = 'occupywallst/base.html'
    return {'OWS_CANONICAL_URL': settings.OWS_CANONICAL_URL,
            'OWS_SCRIPTS': settings.OWS_SCRIPTS,
            'OWS_SCRIPTS_MINIFIED': settings.OWS_SCRIPTS_MINIFIED,
            'DEBUG': settings.DEBUG,
            'base': base}


def notifications(request):
    if request.user.is_authenticated():
        qset = (request.user.notification_set
                .filter(is_read=False)
                .order_by('published'))
        return {'notifications': qset}
    else:
        return {}
