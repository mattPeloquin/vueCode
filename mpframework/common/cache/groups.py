#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Tiered invalidation for system, provider, and sandbox

    Uses version_key cache groups to provide chained invalidation
    of cache groups deleting "upstream" group version keys.

    Sandboxes, Content, and other MPF models have settings that affect how
    each request is loaded. Processing this dynamic configuration for each
    request is prohibitive, so results and HTML fragments are cached.

    Dependencies on cached values can have wide 'downstream' fanout.
    To make invalidation manageable, cached data is tied to invalidation groups.
    All items in a group are invalidated by changing/deleting a version_key
    incorporated into the each data item's cache key.

    Cache groups use namespaces. The default is:

        'tg' (tenant group) for provider/sandbox groups

    Invalidating sandbox, provider, or system version keys invalidates
    ALL 'downstream' KEYS included that version key's namespace and group.

    Each group is uniquely defined by:

        Namespace       (e.g., 'tg', 'cnt', 'twcnt', or other string)
        Group name      (e.g., Model cache_group() or other string)
        Upstream chain  (e.g, Sandbox is separete from Sandbox->Provider)

    The tradeoff - CHAINING REQUIRES MULTIPLE VERSION LOOKUPS
    For example, a Sandbox group chained to Provider group requires 2 cache lookups
    to fully resolve version key, so each cache get of a value needs 3 lookups.
    This is mitigated by using local_small for version lookups.

    Chaining is implemented by storing a random string as the cached value
    of an upstream group version_key, and adding it to key immediately downstream.
    Downstream cache groups repeat the process, creating the chain.
    When an upstream group key is deleted all key names downstream are obsolete
    (after any buffering is expired).
    There is a race condition in intitually setting the random names of the upstream
    version values, but whoever was last will win, and any caching based on
    earlier versions is just invalidated.

    NOTE - The system group is set to false by default to avoid extra version
    round trip for system version check.
    This means any caching which uses the default group but has a dependency on
    system caching will require a cache clear if system is updated.
"""
from django.conf import settings

from . import invalidate_cache_group
from . import cache_version
from .utils import make_full_key


_sys_buffer_age = settings.MP_CACHE_AGE['BUFFER_VERSION_SYSTEM']
_prov_buffer_age = settings.MP_CACHE_AGE['BUFFER_VERSION_PROVIDER']


#--- Global system grouping

def cache_group_system( namespace ):
    """
    System group namespaces can be used directly for system-wide values
    and for cascading invalidation of items that depend on system values.
    """
    group_key = _system_key( namespace )
    return cache_version( group_key, version_prefix=group_key,
                buffered=_sys_buffer_age )

def _system_key( namespace ):
    return make_full_key( 'cgsys', namespace, '' )

def _system_upstream( namespace, system ):
    return cache_group_system( namespace ) if system else namespace

#--- Provider / Sandbox tenant grouping

def cache_group_provider( provider_id, namespace='tg', system=False ):
    """
    Get cache_group_provider key namespace that optionally chains to the
    system invalidation scope.
    """
    upstream = _system_upstream( namespace, system )
    group_key = _provider_key( provider_id, upstream )
    version_prefix = _provider_namespace( provider_id,  upstream )
    return cache_version( group_key, version_prefix=version_prefix,
                buffered=_prov_buffer_age )

def _provider_key( provider_id, upstream ):
    return make_full_key( 'cgp', provider_id, upstream )

def _provider_namespace( provider_id, namespace ):
    return 'p{}{}'.format( provider_id, namespace )

def _provider_upstream( provider_id, namespace, system ):
    if provider_id:
        rv = cache_group_provider( provider_id, namespace, system )
    else:
        rv = _system_upstream( namespace, system )
    return rv

def cache_group_sandbox( sandbox_id, provider_id=None,
            namespace='tg', system=False ):
    """
    Get cache_group_sandbox key namespace that optionally chains upstream
    to provider and/or system scope.
    """
    upstream = _provider_upstream( provider_id, namespace, system )
    group_key = _sandbox_key( sandbox_id, upstream )
    version_prefix = _sandbox_namespace( sandbox_id, upstream )
    return cache_version( group_key, version_prefix=version_prefix )

def _sandbox_key( sandbox_id, upstream ):
    return make_full_key( 'cgs', sandbox_id, upstream )

def _sandbox_namespace( sandbox_id, namespace ):
    return 's{}{}'.format( sandbox_id, namespace )

"""
    To invalidate each group, need to delete the system, provider, or
    sandbox key which stores version used to cache items downstream
    in the call_cache method.
    This forces a new group version_key next time the group is accessed.
     - The invalidation is only in the namespace
     - Both system and non-system cleared for sandbox and provider
"""

def invalidate_group_system( namespace ):
    invalidate_cache_group( _system_key( namespace ) )

def invalidate_group_provider( provider_id, namespace='tg' ):
    down1 = _provider_key( provider_id, _system_upstream( namespace, True ) )
    down2 = _provider_key( provider_id, _system_upstream( namespace, False ) )
    invalidate_cache_group( down1 )
    invalidate_cache_group( down2 )

def invalidate_group_sandbox( sandbox_id, provider_id=None, namespace='tg' ):
    down1 = _sandbox_key( sandbox_id,
                _provider_upstream( provider_id, namespace, True ) )
    down2 = _sandbox_key( sandbox_id,
                _provider_upstream( provider_id, namespace, False ) )
    invalidate_cache_group( down1 )
    invalidate_cache_group( down2 )
