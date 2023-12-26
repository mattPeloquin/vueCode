#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    MPF tenancy managers
"""
from django.conf import settings

from mpframework.common import log
from mpframework.common.model import BaseManager
from mpframework.common.model.related import add_related_fields

from . import TenantQuerySet


class _TenantBaseManager( BaseManager ):
    """
    Ensures tenancy is handled for querysets.
    """

    def get_queryset( self ):
        qs = TenantQuerySet( model=self.model )
        qs = add_related_fields( qs, self.model )
        return qs

    def lookup_queryset( self, sandbox ):
        """
        OVerridable hook for base queryset used for lookup searches
        """
        return self.mpusing('read_replica')\
                    .filter( sandbox=sandbox )

    def limits_ok( self, **kwargs ):
        """
        Placeholder for enforcing policy limits on models.
        This is handled by default for create_obj, while Admin code that
        requires limit hecks will need to call directly.
        """
        return True

    def create_obj( self, **kwargs ):
        """
        Enforce any limit checks.
        """
        if self.limits_ok( **kwargs ):
            return super().create_obj( **kwargs )

# Pass-through manager and queryset methods from TenantManager
TenantBaseManager = _TenantBaseManager.from_queryset( TenantQuerySet )


class _TenantManager( TenantBaseManager ):
    """
    The main tenant manager adds logic for cloning models across tennancy.
    It requires the model to inherit from TenantBaseCloneMixin.
    """

    def clone_object( self, obj, **kwargs ):
        """
        Support copying a model within or across sandboxes.
        Downcasting is used to allow iteration over lists of base classes.
        """
        return obj.downcast_model.clone( **kwargs )

    def clone_sandbox_objects( self, source, target, **filters ):
        """
        Creates copies of all model objects in the TEMPLATE sandbox
        in the TARGET sandbox, by calling clone and clone_fixup.
        Returns a list of the new items in the target
        """
        log.info("CLONING SANDBOX OBJECTS %s: %s -> %s, %s", self.model.__name__,
                source, target, filters)
        rv = []
        try:
            # Create the new objects in target sandbox - note that if the object
            # being cloned needs to adjust it's tenancy key from sandbox,
            # that needs to be done in clone_object overrides
            for source_obj in self.filter( sandbox=source, **filters ):
                self.clone_object( source_obj, sandbox=target )

            # Do any fixup on the new target objects
            for target_obj in self.filter( sandbox=target ):
                target_obj.downcast_model.clone_fixup( source )
                rv.append( target_obj )

        except Exception:
            log.exception("Problem cloning sandbox models: %s -> %s", source, target)
            if settings.MP_TESTING:
                raise
        return rv

# Pass-through manager and queryset methods from TenantManager
TenantManager = _TenantManager.from_queryset( TenantQuerySet )
