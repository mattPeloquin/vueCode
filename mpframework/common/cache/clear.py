#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Cache invalidation

    Local buffer delete is optimization for updates to reflect immediately
    in a request cycle -- VALUE IS STILL BUFFERED ON OTHER SERVERS!
"""
from django.conf import settings
from django.core.cache import caches

from .. import log
from . import cache_version
from .utils import make_full_key
from .utils import make_buffer_key


def invalidate_key( key, cache='default', version=None ):
    """
    Invalidate key by removing from cache and buffers.
    """
    cache = caches[ cache ]
    if isinstance( key, tuple ):
        key, version_group = key
        version = cache_version( version_group )
        key = make_full_key( '', key, version_group )
    _remove_key( key, cache, version )

def invalidate_cache_group( version_key ):
    """
    Invalidates all items in the version_key group by removing the
    version_key from the version cache and buffers.
    Most caching uses this mechanism, based on making version_key calls for
    every cache lookup, allowing groups of items to be invalidated at once.
    """
    log.debug("Invalidate group: %s", version_key)
    _remove_key( version_key, caches['version'], buffer='local_small' )

def _remove_key( key, cache, version=None, buffer=None ):
    """
    Remove the remote key and locally buffered copies.
    """
    buffer_key = make_buffer_key( cache, key, version )
    if buffer:
       caches[ buffer ].delete( buffer_key )
    else:
        # Try all buffers since don't know which one was used
        caches['local_small'].delete( buffer_key )
        caches['local_medium'].delete( buffer_key )
        caches['local_large'].delete( buffer_key )

    log.cache("INVALIDATE( %s %s )", key, version)
    cache.delete( key, version=version )

#--------------------------------------------------------------------
# Invalidation of entire caches

def clear_cache( cache_name ):
    """
    Clear all caching on an entire BACKEND
    This should only be used during ops scenarios, not as part of cache invalidation
    """
    cache = caches[ cache_name ]
    if not settings.MP_TESTING:
        log.warning("====  CLEARING CACHE BACKEND (%s)  ====", cache.key_prefix)
    cache.clear()

def clear_local_buffer():
    """
    This is a special-case function, usually only relevant for making
    dev testing/debug be more responsive to changes,
    as normally willing to accept delay from buffering
    """
    log.debug2("CLEARING LOCAL buffer cache")
    caches['local_small'].clear()
    caches['local_medium'].clear()
    caches['local_large'].clear()
