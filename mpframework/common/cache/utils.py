#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared code for creating keys
"""
from hashlib import sha1

from .. import log
from ..utils import json_dump
from ..utils.fn import key_from_arguments
from .key import make_key


def make_hash( data ):
    """
    Create a hash value stable across machines for any object.
    Takes into account nested dicts with JSON conversion,
    uses IDs for model values, and sha1 since Python hash
    is seeded per process.
    """
    string_val = json_dump( data, expand=False, sort_keys=True )
    return sha1( string_val.encode( 'utf-8', 'replace' ) ).hexdigest()

def make_full_key( prefix, key, version_key ):
    """
    Return key string with namespace prefix and version_key.
    """
    rv = prefix + str(key)
    if version_key:
        rv += '|' + version_key
    return rv

def make_buffer_key( cache, key, version=None ):
    """
    Call backend key fn to add the cache namespace, to recreate the
    key for use with buffered items and deletion.
    """
    return make_key( key, version, cache.key_prefix )

def key_from_fn_sig( version_key, fn_name, args, kwargs ):
    """
    Create memoization key for caching and stashing.
    """
    key = key_from_arguments( args, kwargs )
    hashed_key = sha1( key.encode( 'utf-8', 'replace' ) ).hexdigest()
    log.cache3("key_from_fn_sig args: %s, %s -> %s", fn_name, hashed_key, key)
    return make_full_key( fn_name, hashed_key, version_key )

def get_timeout( cache, timeout ):
    """
    Django cache timeout=None is cache forever,
    MPF timeout=None is to use cache default.
    """
    return timeout or cache.default_timeout
