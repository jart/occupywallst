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

from django.http import HttpResponse


class APIException(Exception):
    def __init__(self, message, results=None):
        self.message = message
        self.results = results

    def __str__(self):
        return self.message

    def __repr__(self):
        return "<APIException: %s>" % (self)


def api_view(function):
    """Decorator that turns a function into a Django JSON API view
    """
    @wraps(function)
    def _api_view(request):
        args = dict(request.REQUEST)
        args['request'] = request
        try:
            res = {'status': 'OK',
                   'message': 'success',
                   'results': function(**args)}
        except APIException, exc:
            res = {'status': 'ERROR',
                   'message': str(exc),
                   'results': getattr(exc, 'results', None)}
        except Exception, exc:
            logging.exception('api request failed')
            res = {'status': 'ERROR',
                   'message': str(exc),
                   'results': getattr(exc, 'results', None)}
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
