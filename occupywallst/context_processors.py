r"""

    occupywallst.context_processors
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tell Django to define certain template variables by default.

"""

from django.conf import settings


def goodies(request):
    return {'OWS_CANONICAL_URL': settings.OWS_CANONICAL_URL}
