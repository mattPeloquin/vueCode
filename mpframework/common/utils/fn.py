#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Function utilities
"""

from . import json_dump


def memoize( fn, memos=None ):
    """
    Returns memoized function.
    Use as decorator to support storage for entire process, or call
    with memos to limit scope and promote garbage collection.
    """
    add_name = memos is not None
    memos = {} if memos is None else memos
    def wrapper( *args, **kwargs ):
        key = key_from_arguments( args, kwargs )
        # Python hash is ok here since memo values are only used
        # within one process
        key = str( hash( key ) )
        if add_name:
            key = fn.__name__ + key
        rv = memos.get( key )
        if not rv:
            rv = fn( *args, **kwargs )
            memos[ key ] = rv
        return rv
    return wrapper

def key_from_arguments( args, kwargs ):
    """
    Provide string for args/kwargs combo for caching.
    """
    rv = ''
    if args or kwargs:
        # First do an optimization pass at the first level to
        # convert items with IDs
        arg_values = { '__args': [ _arg_key( arg ) for arg in args ] }
        for key in kwargs:
            arg_values[ key ] = _arg_key( kwargs[ key ] )
        # Then convert to JSON for repeatable string expansion
        rv = json_dump( arg_values, expand=False, sort_keys=True )
    return rv

def _arg_key( arg ):
    """
    Many objects are models or have a ID for hash optimization (e.g., request)
    so have a go at ID first, otherwise return the obj/value for hashing.
    This assumes any dependencies in caching the object state are reflected
    in the ID, which they should be both for short-term per-process objects
    and distributed cache objects which are invalidated on change.
    """
    return getattr( arg, 'id', arg )
