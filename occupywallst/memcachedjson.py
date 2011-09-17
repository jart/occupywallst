r"""

    occupywallst.memcachedjson
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Alternative Django cache backend.

"""

try:
    import simplejson as json
except ImportError:
    import json

from django.core.cache import get_cache
from django.core.cache.backends.memcached import MemcachedCache
from django.contrib.sessions.backends import cache as session_cache


class SessionStore(session_cache.SessionStore):
    def __init__(self, session_key=None):
        self._cache = get_cache('json')
        super(SessionStore, self).__init__(session_key)


class MemcachedCacheJSON(MemcachedCache):
    """Memcache store with JSON serialization

    We want node.js applications to be able to read the stuff Django
    stores to memcached so instead of pickling the data we'll
    serialize it to json.

    This is kind of a hack because looking at python-memcached's
    source it seems *really* intent on using pickle.
    """
    @property
    def _cache(self):
        if getattr(self, '_client', None) is None:
            self._client = self._lib.Client(self._servers,
                                            pickler=Pickler,
                                            unpickler=Unpickler)
        return self._client


class Pickler(object):
    def __init__(self, fp, *args, **argv):
        self.fp = fp

    def dump(self, obj):
        json.dump(obj, self.fp)


class Unpickler(object):
    def __init__(self, fp, *args, **argv):
        self.fp = fp

    def load(self):
        return json.load(self.fp)
