#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Implementation for MPF memoization caching/buffering,
    which is the primary mechanism for caching results.

    Dill is used explicitly here to avoid serialization issues
    with the default Pickle implementation.

    SECURE - Using pickle for caching (and queue/spooling) should
    be safe since there is no vector to replace the bitstream that
    deserialized. Some pickled objects have strings from untrusted
    sources (user, api, etc.). Conceivably, a string embedded
    in an object could hijack deserialization.
    This does not seem to be a current exploit, but if it became a
    risk, the mitigation is to covert all caching (and queue/spooling)
    to only use string/JSON data.
    This removes some convenience of @cache_rv in particular, but many
    performance sensitive areas are already transmit specific string/JSON
    information to capture persistence instead of pickling entire object.

    Extends and narrows Django version invalidation to provide
    invalidation of groups via version keys. Instead of a cache key's
    version field incrementing a number, a version_key is a cache key
    to another unique cached value. The value for version_key is used
    in the key the version string for the main value to be returned.

    The downside is TWO CACHE GETS are needed for retrievals (or more
    if dependency chains of versions are used).
    This overhead is offset by local buffering.

    Caching has overhead so is intended for larger chunks vs. many
    fine-grained items. What to cache should be driven by measurement.
"""
import pickle
from django.conf import settings
from django.core.cache import caches

from .. import log
from .version import cache_version
from .utils import make_buffer_key
from .utils import get_timeout


def cache_function( wrapped_fn, key, cache='default', timeout=None,
            version_key=None, buffered='local_large', buffer_timeout=None,
            no_set=False, punch_through=False ):
    """
    Calls 'wrapped_fn' and caches return value.

    Buffering reduces traffic for high-frequency checks by looking at local
    cache before the distributed cache. Buffering cannot be cleared across
    servers, so only use with versioned items or short timeouts.

    version_key supports optional invalidation of a group of cached items
    by looking up a version value to use with 'key'. This requires an extra
    cache call, so uses local buffering to reduce overhead, so...
        NO INVALIDATION occurs within BUFFER_VERSION timeout.

    timeout - override default lifetime in distributed
    buffer_timeout - overide default buffer lifetime
    punch_through - skips cache/buffer gets and forces wrapped_fn call
    no_set - prevents distributed cache set; supports creation of
        cache only checks that look for value placed by another
        function and return default value if not there.
    """
    cache = caches[ cache ]

    # If version, get from version cache if active or create new
    version = cache_version( version_key ) if version_key else None

    # If value is in local buffer, use it
    if not punch_through:
        buffered_value = _buffer_get( buffered, cache, key, version )
        if buffered_value:
            return buffered_value

    # "op" used with debug logging, but hit in prod is minimal
    op = "NOP"

    # Values in both distributed cache and buffer are picled bytes;
    # keep track of both to avoid unnecessary packing/unpacking
    packed_rv = ''
    rv = None

    # Does the cache have the current value for this version of the key?
    if not punch_through:
        try:
            packed_rv = cache.get( key, version=version )
            if packed_rv is not None:
                op = "HIT"
                rv = pickle.loads( packed_rv )
        except Exception:
            log.exception("CACHE get: %s, version=%s", key, version)
            if settings.MP_DEV_EXCEPTION:
                raise

    # If not cached, execute call
    if rv is None:

        rv = wrapped_fn()

        # Set the value in the distributed cache
        if rv is not None and not no_set:
            try:
                packed_rv = pickle.dumps( rv )
                timeout = get_timeout( cache, timeout )

                cache.set( key, packed_rv, version=version, timeout=timeout )

                if log.debug_on():
                    op = "SET(%s)" % timeout if timeout else "SET"
                    op += ' ' + str(len(packed_rv))
            except Exception:
                log.exception("CACHE set: %s -> %s", key, str(rv)[:256])
                if settings.MP_DEV_EXCEPTION:
                    raise

    # Buffer value from distributed cache or wrapped_fn
    if rv is not None:
        _buffer_set( buffered, packed_rv, cache, key, version, buffer_timeout )

    if log.debug_on():
        log.cache("CACHE %s %s %s( %s : %s ) %s",
            op, 'b' if buffered else '', cache.key_prefix,
            key, '%s<-%s' % ( version, version_key ) if version_key else version,
            '-> %s...' % str(packed_rv)[:128] if log.debug_on() > 1 else '')
    return rv

def _buffer_get( buffered, cache, key, version ):
    """
    Check the local buffer for the cache value
    """
    if buffered:
        buffer_key = make_buffer_key( cache, key, version )
        try:
            value = caches[ buffered ].get( buffer_key )
            if value is not None:
                value = pickle.loads( value )

            if log.debug_on():
                log.cache2("BUFFER %s(%s) %s", "MISS" if value is None else "HIT",
                    buffer_key, "%s..." % str(value)[:64] if log.debug_on() > 1 else '')

            return value

        except Exception:
            log.exception("CACHE BUFFER get: %s", buffer_key)
            if settings.MP_DEV_EXCEPTION:
                raise

def _buffer_set( buffered, value, cache, key, version, timeout ):
    """
    Add value to local buffer.
    """
    if buffered:
        buffer_key = make_buffer_key( cache, key, version )
        try:
            timeout = get_timeout( caches[ buffered ], timeout )
            caches[ buffered ].set( buffer_key, value, timeout=timeout )

            if log.debug_on():
                log.cache2("BUFFER SET(%s, %ss): %s...", buffer_key, timeout,
                        "%s..." % str(value)[:64] if log.debug_on() > 1 else '')
        except Exception:
            log.exception("CACHE BUFFER set: %s", buffer_key)
            if settings.MP_DEV_EXCEPTION:
                raise
