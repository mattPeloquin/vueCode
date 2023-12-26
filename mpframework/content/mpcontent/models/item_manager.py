#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Item manager adds support for item-specific behavior
"""

from .base.manager import ContentQuerySet
from .base.manager import ContentManager


class ItemQuerySet( ContentQuerySet ):

    def filter_items( self, *args, **kwargs ):
        """
        HACK - reference trees to allow DB exclusion
        """
        from .tree import Tree
        return self.exclude( _django_ctype=Tree.get_django_ctype() )\
                    .filter( *args, **kwargs )


class _ItemManager( ContentManager ):

    def _get_queryset( self ):
        return ItemQuerySet( model=self.model )

    def lookup_queryset( self, sandbox ):
        """
        Don't include trees or retired items in autolookups
        """
        return self.filter_items( sandbox=sandbox, workflow__in='PBD' )

# Use from_queryset to include both custom manager and queryset methods
ItemManager = _ItemManager.from_queryset( ItemQuerySet )
