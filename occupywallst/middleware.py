r"""

    occupywallst.middleware
    ~~~~~~~~~~~~~~~~~~~~~~~

    Django middleware definitions.

"""

import traceback

from django.utils.cache import add_never_cache_headers


class PrintException(object):
    def process_exception(self, request, exception):
        traceback.print_exc()


class NeverCache(object):
    def process_response(self, request, response):
        add_never_cache_headers(response)
        return response
