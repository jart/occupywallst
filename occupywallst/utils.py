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
from decimal import Decimal
from functools import wraps
from datetime import datetime

from django.db import transaction
from django.http import HttpResponse
from django.views.decorators.http import require_POST


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
    @require_POST
    @transaction.commit_manually
    def _api_view(request):
        args = {}
        for key in request.POST:
            args[key] = request.POST[key]
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
        logger.info("api %s returning %s: %s" %
                    (request.path, res['status'], res['message']))
        return _as_json(res)
    return _api_view


def _as_json(data):
    """Turns API result into JSON data
    """
    data['results'] = sanitize_json(data['results'])
    response = HttpResponse(json.dumps(data), mimetype="application/json")
    return response


def jsonify(value, **json_argv):
    return json.dumps(sanitize_json(value), **json_argv)


def sanitize_json(value):
    if hasattr(value, 'as_dict'):
        return sanitize_json(value.as_dict())
    elif hasattr(value, 'timetuple'):
        return jstime(value)
    elif isinstance(value, Decimal):
        return str(value)
    elif isinstance(value, basestring):
        return value
    elif isinstance(value, dict):
        for k in value:
            value[k] = sanitize_json(value[k])
        return value
    elif hasattr(value, '__iter__'):
        return [sanitize_json(i) for i in value]
    else:
        return value


def timesince(timestamp):
    delta = (datetime.now() - timestamp)
    seconds = delta.days * 60 * 60 * 24 + delta.seconds
    if seconds <= 60:
        x = seconds
        s = ('second', 'seconds')
    elif seconds <= 60 * 60:
        x = int(round(seconds / 60.0))
        s = ('minute', 'minutes')
    elif seconds <= 60 * 60 * 24:
        x = int(round(seconds / 60 / 60))
        s = ('hour', 'hours')
    elif seconds <= 60 * 60 * 24 * 30:
        x = int(round(seconds / 60 / 60 / 24))
        s = ('day', 'days')
    else:
        x = int(round(seconds / 60 / 60 / 24 / 30))
        s = ('month', 'months')
    return "%d %s" % (x, s[x != 1])


def jstime(dt):
    """Convert datetime object to javascript timestamp (milliseconds
    since UTC UNIX epoch)
    """
    ts = int(time.mktime(dt.timetuple())) * 1000
    if hasattr(dt, 'microsecond'):
        ts += dt.microsecond / 1000
    return ts
