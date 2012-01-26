r"""

    occupywallst.util
    ~~~~~~~~~~~~~~~~~

    Miscellaneous functions that help you.

"""

import json
import time
import logging
import traceback
from decimal import Decimal
from functools import wraps
from datetime import datetime, timedelta

from django.conf import settings
from django.db import transaction
from django.http import HttpResponse
from django.utils.tzinfo import LocalTimezone
from django.utils.translation import ungettext, ugettext


logger = logging.getLogger(__name__)


class APIException(Exception):
    """Causes API wrapper to return an error result"""
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

    API functions that have side-effects should be wrapped in a
    ``require_POST`` decorator in your ``url.py`` file to ensure CSRF
    protection, otherwise they should be wrapped in ``require_GET``.
    """
    @wraps(function)
    @transaction.commit_manually
    def _api_view(request):
        args = {}
        args.update(request.REQUEST)
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
            traceback.print_exc()
            logger.exception('api request failed')
            res = {'status': 'ERROR',
                   'message': 'system malfunction',
                   'results': []}
            transaction.rollback()
            if getattr(settings, 'TEST_MODE', False):
                raise
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
    """Turns API result into JSON data"""
    data['results'] = sanitize_json(data['results'])
    if settings.DEBUG:
        content = json.dumps(data, indent=2) + '\n'
    else:
        content = json.dumps(data)
    response = HttpResponse(content, mimetype="application/json")
    return response


def jsonify(value, **argv):
    return json.dumps(sanitize_json(value), **argv)


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


def timesince(d, now=None):
    """Shortened version of django.utils.timesince.timesince"""
    chunks = (
        (60 * 60 * 24 * 365, lambda n: ungettext('year', 'years', n)),
        (60 * 60 * 24 * 30, lambda n: ungettext('month', 'months', n)),
        (60 * 60 * 24 * 7, lambda n: ungettext('week', 'weeks', n)),
        (60 * 60 * 24, lambda n: ungettext('day', 'days', n)),
        (60 * 60, lambda n: ungettext('hour', 'hours', n)),
        (60, lambda n: ungettext('minute', 'minutes', n))
    )
    # Convert datetime.date to datetime.datetime for comparison.
    if not isinstance(d, datetime):
        d = datetime(d.year, d.month, d.day)
    if now and not isinstance(now, datetime):
        now = datetime(now.year, now.month, now.day)
    if not now:
        if d.tzinfo:
            now = datetime.now(LocalTimezone(d))
        else:
            now = datetime.now()
    # ignore microsecond part of 'd' since we removed it from 'now'
    delta = now - (d - timedelta(0, 0, d.microsecond))
    since = delta.days * 24 * 60 * 60 + delta.seconds
    if since <= 0:
        # d is in the future compared to now, stop processing.
        return u'0 ' + ugettext('minutes')
    for i, (seconds, name) in enumerate(chunks):
        count = since // seconds
        if count != 0:
            break
    return ugettext('%(number)d %(type)s') % {
        'number': count, 'type': name(count)}


def jstime(dt):
    """Convert datetime object to javascript timestamp

    In javascript, timestamps are represented as milliseconds since
    the UNIX epoch in UTC.
    """
    ts = int(time.mktime(dt.timetuple())) * 1000
    if hasattr(dt, 'microsecond'):
        ts += dt.microsecond / 1000
    return ts
