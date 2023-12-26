#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Model support for caching
"""

from .. import log
from ..cache import invalidate_cache_group
from ..cache import clear_stashed_methods
from ..cache import cache_version


class CachedModelMixin:
    """
    Models that participate in direct caching must inherit from this class.
    Assumes BaseModel is base class.
    """
    _caching = True
    _clear_cache_field_names = ()
    _clear_cache_names = ()

    def save( self, *args, **kwargs ):
        """
        Save and invalidate
        """
        invalidate = kwargs.pop( 'invalidate', True )
        super().save( *args, **kwargs )
        if invalidate:
            self.invalidate()

    def invalidate( self ):
        self.invalidate_group()
        self.clear_stash()

    def clear_for_cache( self ):
        """
        Called before caching to strip stashed items, cached querysets, and
        any other info that shouldn't be pickled into the cache.
        """
        self.clear_stash()
        for name in self._clear_cache_names:
            setattr( self, name, None )
        for name in self._clear_cache_field_names:
            self._clear_dj_names_for_cache( name )

    # HACK - based on Django queryset cache names
    def _clear_dj_names_for_cache( self, name ):
        for pattern in self._django_cached_patterns:
            cached_name = pattern.format( name )
            if hasattr( self, cached_name ):
                delattr( self, cached_name )
                log.debug_on() and log.cache3("CACHED NAME CLEAR %s -> %s (%s)",
                                            cached_name, self.unique_key, id(self))
    _django_cached_patterns = (
            '_{}_cache', '_m2m_{}_cache', '__m2m_reverse_{}_cache' )

    def clear_stash( self ):
        clear_stashed_methods( self )

    @property
    def cache_group( self ):
        """
        Default model cached grouping is model name/id
        """
        return 'mcg-' + self.unique_key

    def invalidate_group( self ):
        """
        Will invalidate any data in the cache group
        """
        invalidate_cache_group( self.cache_group )

    @property
    def cache_group_version( self ):
        """
        Easy access to current invalidation version
        """
        return cache_version( self.cache_group )
