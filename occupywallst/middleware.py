r"""

    occupywallst.middleware
    ~~~~~~~~~~~~~~~~~~~~~~~

    Django middleware definitions.

"""

import traceback


class PrintException(object):
    def process_exception(self, request, exception):
        traceback.print_exc()
