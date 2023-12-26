#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Integrating uwsgi cache with Django caching

    SECURE - See discussion of pickle in common/cache/call_cache.py

    PORTIONS ADAPTED FROM OPEN SOURCE:
      https://github.com/unbit/django-uwsgi/blob/master/django_uwsgi/
"""
import pickle
from django.core.cache.backends.base import BaseCache
from django.utils.encoding import force_bytes

from .. import log

try:
    import uwsgi
    _test_for_valid_import = uwsgi.SPOOL_RETRY

    class UwsgiCache( BaseCache ):
        """
        uWSGI cache backend
        """
        def __init__( self, server, params ):
            BaseCache.__init__( self, params )
            self._cache = uwsgi
            self._server = server

        def exists( self, key ):
            return self._cache.cache_exists( force_bytes(key), self._server )

        def add( self, key, value, timeout=True, version=None ):
            full_key = self.make_key( key, version=version )
            if self.exists( full_key ):
                return False
            self._set( full_key, value, timeout )
            return True

        def get( self, key, default=None, version=None ):
            full_key = self.make_key( key, version=version )
            val = self._cache.cache_get( force_bytes(full_key), self._server )
            if val is None:
                return default
            val = force_bytes( val )
            return pickle.loads( val )

        def _set( self, full_key, value, timeout ):
            """
            Match django semantics to uwsgi
            """
            # Explicitly passing in timeout=None will set a non-expiring timeout.
            # Passing in timeout=0 will set-and-expire-immediately the value.
            if timeout is True:
                uwsgi_timeout = self.default_timeout
            elif timeout is None or timeout is False:
                uwsgi_timeout = 0
            elif timeout == 0:
                uwsgi_timeout = -1
            else:
                uwsgi_timeout = timeout
            # uWSGI's default cache mode will throw exception of the
            # blocksize of payload is exceeded, which is not a fatal error
            # since uWSGI is only used for temporary caching
            try:
                self._cache.cache_update( force_bytes( full_key ),
                        pickle.dumps( value ), uwsgi_timeout, self._server )
            except Exception as e:
                log.info("ERROR uWSGI cache set failed: %s -> %s", full_key, e)

        def set( self, key, value, timeout=True, version=None ):
            full_key = self.make_key( key, version=version )
            self._set( full_key, value, timeout )

        def delete( self, key, version=None ):
            full_key = self.make_key( key, version=version )
            self._cache.cache_del( force_bytes(full_key), self._server )

        def close( self, **kwargs ):
            pass

        def clear( self ):
            self._cache.cache_clear( self._server )

except ( ImportError, AttributeError ):

    # Should only try to import if UWSGI is running, so cause fatal
    # error when backend is loaded if uwsgi is not available
    UwsgiCache = None
