#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Memoization for models by "stashing" values
    Stashing == PER-SERVER-PROCESS memory caching

      0) Stashing (and caching) adds overhead, trading memory use and some
      time if keys for function calls have complex or changing arguments.
      Only use for expensive operations where value is useful.

      1) Distributed cache mechanisms are default for caching most
      expensive operations, as they share across all processes.

      2) To avoid network latency from small high frequency items
      MPF has per-server BUFFERING and per-process STASHING:

        -- Stashing stores method return values within models, usually
           for request/response cycle or long-lived option objects.
           There is no aging or invalidation other than complete reset.

        -- Buffering is shared across a server. As with caching values are
           pickled, and there is aging and invalidation.

        -- BUFFERING is ADDED to distributed caching, while
           STASHING should be used INSTEAD of caching

    Be careful with per-process memory for stashing; there can be a lot of
    processes on a relatively small machine, so memory amounts add up.
"""
from functools import wraps

from .. import log
from .utils import key_from_fn_sig


STASH_NAME = '__mp_stash'


def clear_stashed_methods( obj ):
    """
    Remove all stashes values from an object
    """
    if hasattr( obj, STASH_NAME ):
        delattr( obj, STASH_NAME )
        log.debug_on() and log.cache3("STASH CLEAR %s addr:%s",
                                        obj.__class__.__name__, id(obj))

def stash_method_rv( func=None ):
    """
    Decorator to memoize object method return values

    NO AGING FOR OBJECT STASHING --
           Value is stashed for life of object or until refreshed!

    Only stash methods that have no side effects beyond the object.
    Methods that modify the state of the object in a way that will persist
    for the life of the object are ok, but be careful.

    Stashing automatically turns args and kwargs into hashed keys; don't
    use if there is a lot of variance, or that is expensive or unworkable.

    Stashed values are typically cleared before caching an object, but do
    use stable sha1 hash so can be cached with object.
    """
    def decorator( fn ):
        @wraps( fn )
        def wrapper( self, *args, **kwargs ):
            op = "NOP"
            stash = getattr( self, STASH_NAME, {} )

            stash_name = key_from_fn_sig( '', fn.__name__, args, kwargs )
            rv = stash.get( stash_name )

            if rv is not None:
                op = "GET"
            else:
                rv = fn( self, *args, **kwargs )
                if rv is not None:
                    op = "SET"
                    stash[ stash_name ] = rv
                    setattr( self, STASH_NAME, stash )

            if log.debug_on():
                log.cache3("STASH %s %s%s, addr:%s",
                       op, self.__class__.__name__, stash_name, id(self))
            return rv
        return wrapper
    return decorator( func ) if func else decorator

