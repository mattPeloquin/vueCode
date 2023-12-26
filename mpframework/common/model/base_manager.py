#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Create Pass-through manager with queryset methods
"""
from django.db import models
from django.conf import settings

from .. import log
from . import BaseQuerySet


class _BaseManager( models.Manager ):

    def get_queryset( self ):
        return BaseQuerySet( model=self.model )

    def all( self ):
        """
        Make sure default managers always use filter call,
        including for related manager, where Django calls all()
        """
        return self.get_queryset().filter()

    def all_rows( self ):
        """
        Support queryset operations that need to look past tennancy
        """
        return super().all()

    def create_obj( self, **kwargs ):
        """
        Common manager method for most non-Admin creation of model instances, to
        support easy polymorphic creation.
        Many model instances could just instantiate the model class, but some
        require dependencies or other fixup work. Use this method to keep
        that knowledge with the manager.
        Admin creates with ModelForms, so may need to keep creation in
        sync for both pathways.
        """
        log.debug("Creating new %s: %s", self.model.__name__, kwargs)
        rv = self.model( **kwargs )
        rv.save()
        return rv

BaseManager = _BaseManager.from_queryset( BaseQuerySet )
