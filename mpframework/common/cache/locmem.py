#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Dev/Test local cache support
"""
from django.core.cache.backends.locmem import LocMemCache


class mpLocMemCache( LocMemCache ):
    """
    Dev version of local cache that allows cache dumping and
    supports some django-redis extensions.
    This is NOT intended to be performant with large caches.
    """

    def iter_keys( self, search, itersize=None, **kwargs ):
        items = 0
        # The key matching may not match Redis exactly
        searches = search.strip('*').split('*')
        for key in self._cache:
            if itersize and items >= itersize:
                return
            matches = [ s for s in searches if s in key ]
            if matches and all( matches ):
                yield key

    def get_many( self, keys, **kwargs ):
        rv = {}
        for key in keys:
            value = self._cache.get( key )
            if value:
                rv[ key ] = value
        return rv

    def local_keys( self, key_includes=None ):
        return [ k for k, v in self.local_items( key_includes ) ]

    def local_items( self, key_includes=None ):
        return [ (k, v) for (k, v) in self._cache.items() if
                    not key_includes or key_includes in k ]

    def local_keys( self, key_includes=None ):
        return [ k for k, v in self.local_items( key_includes ) ]
