r"""

    occupywallst.util
    ~~~~~~~~~~~~~~~~~

    Miscellaneous functions that help you.

"""

import csv
import json
import time
import logging
import StringIO
from functools import wraps
from decimal import Decimal

from django.db import transaction
from django.http import HttpResponse


logger = logging.getLogger(__name__)


class APIException(Exception):
    """Causes API wrapper to return an error result.
    """
    def __init__(self, message, results=[]):
        self.message = message
        self.results = results

    def __str__(self):
        return self.message

    def __repr__(self):
        return "<APIException: %s>" % (self)


def api_view(function):
    """Decorator that turns a function into a Django JSON API view

    Your function must return a list of results which are expressed as
    normal Python data structures.  If something bad happens you
    should raise :py:class:`APIException`.

    This function also catches general exceptions to ensure the client
    always receives data in JSON format.
    """
    @wraps(function)
    @transaction.commit_manually
    def _api_view(request):
        args = dict(request.REQUEST)
        args['request'] = request
        args['user'] = request.user
        try:
            data = list(function(**args))
        except APIException, exc:
            res = {'status': 'ERROR',
                   'message': str(exc),
                   'results': list(getattr(exc, 'results', None))}
            transaction.rollback()
        except Exception, exc:
            logger.exception('api request failed')
            res = {'status': 'ERROR',
                   'message': 'system malfunction',
                   'results': []}
            transaction.rollback()
        else:
            if data:
                res = {'status': 'OK',
                       'message': 'success',
                       'results': data}
            else:
                res = {'status': 'ZERO_RESULTS',
                       'message': 'no data returned',
                       'results': data}
            transaction.commit()
        return _as_json(res)
    return _api_view


def _as_json(data):
    """Turns API result into JSON data
    """
    def sanitize(v):
        if hasattr(v, 'timetuple'):
            return jstime(v)
        elif isinstance(v, Decimal):
            return str(v)
        elif isinstance(v, basestring):
            return v
        elif isinstance(v, dict):
            for k in v:
                v[k] = sanitize(v[k])
            return v
        elif hasattr(v, '__iter__'):
            return [sanitize(i) for i in v]
        else:
            return v
    data['results'] = sanitize(data['results'])
    response = HttpResponse(json.dumps(data), mimetype="application/json")
    return response


def jstime(dt):
    """Convert datetime object to javascript timestamp (milliseconds
    since UTC UNIX epoch)
    """
    ts = int(time.mktime(dt.timetuple())) * 1000
    if hasattr(dt, 'microsecond'):
        ts += dt.microsecond / 1000
    return ts
