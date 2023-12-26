#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Cache key support

    This file is imported by Django cache code so cannot have dependencies
    on cache files since they import the Django cache module
"""
from hashlib import sha1


def key_function( key, prefix, version ):
    """
    Match the signature of the cache KEY_FUNCTION config; which
    is different from arg defaults used for backend's make_key
    """
    return make_key( key, version, prefix )


def make_key( key, version=None, prefix=None, hash=False ):
    """
    Override Django's default cache key function to provide control of string,
    versioning, and optional hasing of key.
    key is passed by MPF caching, key_prefix comes from cache.key_prefix
    """
    assert key
    key_frag = []
    prefix and key_frag.append( str(prefix) )
    key_frag.append( str(key) )

    # Only use version if added - MPF manages key version invalidation,
    # so in some cases want option to not use it
    version and key_frag.append( str(version) )
    key_raw = ':'.join( key_frag )

    # Replace spaces (memcache doesn't like, easier to read in debug)
    key_raw = key_raw.replace( ' ', '_' )

    # Hash if requested
    final_key = sha1( key_raw.encode( 'utf-8', 'replace' )
                ).hexdigest() if hash else key_raw

    return final_key

def make_hashed_key( *args, **kwargs ):
    kwargs['hash'] = True
    return make_key( *args, **kwargs )
