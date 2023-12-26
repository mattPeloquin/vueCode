#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Cache memoization for function return values
"""
from functools import wraps

from .call_cache import cache_function
from .utils import key_from_fn_sig
from .utils import make_full_key


def cache_rv( func=None, keyfn=None, group=None, keyname=None, **options ):
    """
    Decorator factory, returns a decorator to cache function return values.

    If no options are provided uses key_from_fn_sig to create unique key with the
    function name and its arguments, and a group/version_key using function name.

    Only use with pure functions that have no side effects, including any state
    change to objects or mutable arguments.

    "keyfn" is called with same arguments as wrapped function, may return:
     - tuple: ( key, version_key ) key is string, version_key processed as below
     - string: used as key, KEYFN NAME used for version_key; don't use with lambdas!
     - None aborts caching

    version_key may be a callable, tuple, named option, or value:
     - If callable, called with same args as wrapped function
     - 'cache_group' tries to call cache_group property object
     - '' disables version cache group processing
    The value (passed in or from callable) is a string for version_key

    "group" provides version_key ONLY IF keyfn IS None

    NOTE - the final key for cached value combines version_key with key, so there
    isn't any need to include the same namespace information in both.

    "keyname" is string overriding default of function name in keys, used to:
     - Share a keyfn between functions, while caching results separately
     - Create functions with no_set option that only check for value in cache

    All items sharing the version_key are invalidated together so make
    sure result is unique as intended.

    "func" is for passing optional arguments to the decorator

    See call_cache for caching options.
    """
    def decorator( fn ):
        @wraps( fn )
        def wrapper( *args, **kwargs ):
            key_name = keyname if ( keyname or keyname == '' ) else fn.__name__

            # If custom keyfn provided, use it for key and validation group
            if keyfn:
                _key = keyfn( *args, **kwargs )

                # Abort caching at request of dynamic keyfn
                if _key is None:
                    return fn( *args, **kwargs )

                if isinstance( _key, tuple ):
                    key, version_key = _key
                else:
                    key = _key
                    version_key = keyfn.__name__

            # Otherwise create from group or defaults
            else:
                version_key = group

            # Get version key string and do any callable fixups
            version_key, key_name = _resolve_version_key( version_key, key_name,
                        *args, **kwargs )
            options['version_key'] = version_key

            # Create final cache key from keyfn value or function signature
            if keyfn:
                key = make_full_key( key_name, key, version_key )
            else:
                key = key_from_fn_sig( version_key, key_name, args, kwargs )

            return cache_function( lambda: fn(*args,**kwargs), key, **options )

        return wrapper
    return decorator( func ) if func else decorator

def _resolve_version_key( group, key_name, *args, **kwargs ):
    """
    Resolve the version_key group for the cache_rv decorator as
    described in the cache_rv comments.
    """
    if group is None:
        # If no group, use key_name in group, and blank so it won't be
        # redundant in the main key
        return key_name, ''

    # First resolve any callables
    if callable( group ):
        group = group( *args, **kwargs )
    elif group == 'cache_group':
        group = args[0].cache_group

    # Then convert group into version key
    version_key = str( group )

    return version_key, key_name
