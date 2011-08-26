r"""

    occupywallst.middleware
    ~~~~~~~~~~~~~~~~~~~~~~~

    Django middleware definitions.

"""

import traceback

from django.db import connection
from django.template import Template, Context
from django.utils.cache import add_never_cache_headers


class PrintException(object):
    def process_exception(self, request, exception):
        traceback.print_exc()


class NeverCache(object):
    def process_response(self, request, response):
        add_never_cache_headers(response)
        return response


class XForwardedForMiddleware(object):
    """Replace ``REMOTE_ADDR`` with ``HTTP_X_FORWARDED_FOR``

    When reverse proxying from nginx, we receive a tcp connection from
    localhost which isn't the client's real ip address.  Normally
    reverse proxies are configured to set the ``X-Forwarded-For``
    header which gives us the actual client ip.
    """

    def process_request(self, request):
        if 'HTTP_X_FORWARDED_FOR' in request.META:
            request.META['REMOTE_ADDR'] = request.META['HTTP_X_FORWARDED_FOR']
            request.META['REMOTE_HOST'] = None


class SQLInfoMiddleware(object):
    """Add query statistics to end of HTML responses
    """

    def process_response(self, request, response):
        if not response['Content-Type'].startswith('text/html'):
            print response['Content-Type']
            return response
        toto = 0.0
        queries = []
        for query in connection.queries:
            toto += float(query['time'])
            sql = (query['sql']
                   .replace(' FROM ', '\n\nFROM ')
                   .replace(' WHERE ', '\n\nWHERE ')
                   .replace(' ORDER ', '\n\nORDER ')
                   .replace(' INNER JOIN ', '\n\nINNER JOIN ')
                   .replace(' LEFT OUTER JOIN ', '\n\nLEFT OUTER JOIN ')
                   .replace('; args=( ', ';\n\nargs=(')
                   .strip())
            queries.append({'time': query['time'], 'sql': sql})
        tpl = Template(r'''
          <div id="sql-info" class="hider">
            <div class="info toggle">
              <span>Query Count</span> <strong>{{ count }}</strong>
              <span>Total Time</span> <strong>{{ time }}</strong>
            </div>
            <div class="hidden">
              {% for query in queries %}
                <div class="item">
                  <p><strong>{{ query.time }}</strong></p>
                  {{ query.sql|linebreaks }}
                </div>
              {% endfor %}
            </div>
          </div>
        ''')
        ctx = Context({'queries': queries,
                       'count': len(queries),
                       'time': toto})
        response.content = response.content + tpl.render(ctx).encode('utf8')
        return response
