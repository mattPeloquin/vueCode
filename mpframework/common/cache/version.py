#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Cache group version key suppport

    MPF uses random strings as version keys for cache group invalidation.
    See call_cache.py for more details.
"""
from django.conf import settings
from django.core.cache import caches

from .. import log
from ..utils import get_random_key
from .utils import make_buffer_key
from .utils import get_timeout

_cache = caches['version']
_buffer = caches['local_small']

"""
    Version Key Length
    The maximum collision scope for these keys is across a cache group of system,
    provider, content, or sandbox, and how often the group values are
    invalidated in the version cache expiration time window.
    As per Birthday Paradox, an 8 len has 0.1% chance of conflict at 600K entries,
    which should be plenty, and keep version tags accessible for debugging.
"""
VERSION_KEY_LEN = 8


def cache_version( key, version_prefix='', version_fn=None, force_set=False,
            buffered=settings.MP_CACHE_AGE['BUFFER_VERSION'], timeout=None ):
    """
    Get or create value to use as a cache item's version.
    Versions are special cached strings used in other cache keys for invalidation
    (as MPF cache groups, cached urls, Django cache versions).
    Returns data (usually string) stored for the version value.

    "key" is the VERSION KEY that represents the invalidation group.

    "version_prefix" is prefix used if version_fn is not provided. It is
    combined with a random string and supports chaining version groups
    by building up version names from upstream versions.

    "version_fn" is function that returns string instead of version_prefix
    to include in the version name; return False to prevent creation of
    new version if one doesn't exist.

    "buffered" - Default behavior is to check local version buffer before
    the distributed cache:
       - Default will buffer version for BUFFER_VERSION seconds.
         NO VERSION INVALIDATION ON SERVER OCCURS IN WINDOW
       - Set to a different integer to change version buffer age
       - Set to False to punch-through versioning buffer

    "timeout" changes the distributed cache version timeout from default.
    """
    assert key
    try:
        # First check local buffer (if not forcing set)
        if buffered:
            buffer_key = make_buffer_key( _cache, key )
            version = not force_set and _buffer.get( buffer_key )
            if version:
                log.cache3("VERSION BUFFER(%s) %s", buffer_key, version)
                return version

        # Next try to get from distributed cache (if not forcing set)
        version = not force_set and _cache.get( key )
        if version:
            log.cache2("VERSION GET(%s) %s", key, version)

        # No version in cache, make new version
        else:
            version = version_fn() if version_fn else None
            if version is None:
                version = get_random_key( VERSION_KEY_LEN )
                if version_prefix:
                    version = '{}({})'.format( version_prefix, version )
            if version:
                timeout = get_timeout( _cache, timeout )
                if log.debug_on():
                    log.debug("CACHE VERSION(%s) %s%s -> %s", key,
                            " time:%s" % timeout if timeout else "",
                            " force" if force_set else "", version)

                # Version keys are placed into cache without Django versions
                _cache.set( key, version, timeout=timeout )

        # Only set in the local buffer if new or came from distributed
        # cache -- if set when from buffer would perpetuate infinitely
        if buffered and version:
            _buffer.set( buffer_key, version, timeout=buffered )

        return version

    except Exception:
        log.exception("CACHE VERSION: %s", key)
        if settings.MP_DEV_EXCEPTION:
            raise
