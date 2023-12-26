#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Base class for ProviderOptional models
"""
from django.db import models

from mpframework.common.model import BaseModel
from mpframework.common.model import CachedModelMixin
from mpframework.common.cache.stash import stash_method_rv
from mpframework.common.cache.groups import cache_group_system
from mpframework.common.cache.groups import cache_group_provider
from mpframework.common.cache.groups import invalidate_group_system
from mpframework.common.cache.groups import invalidate_group_provider

from .tenant_clone import TenantCloneMixin


class ProviderOptionalModel( TenantCloneMixin, CachedModelMixin, BaseModel ):
    """
    For models that can either be:
     - Created by root and seen as read-only by all providers
     - Created and modified by specific providers

    All ProviderOptional models use caching, due to expense of
    system-wide use.

    To use with MPF queryset tenant filtering, pass a provider
    with "_provider=xyz", which will check for both cases.
    """
    provider_optional = models.ForeignKey( 'tenant.Provider', models.CASCADE,
                blank=True, null=True )

    class Meta:
        abstract = True

    # Used to manage shared tenant functionality
    _tenancy_type = 'provider_optional'

    @property
    def cache_group( self ):
        """
        Tie all instances of ProviderOptional to provider or system cache group
        to invalidate cached items for any derived classes.
        """
        if self.is_system:
            return cache_group_system( namespace='tg' )
        else:
            return cache_group_provider( self.provider_optional_id, system=True )

    def invalidate_group( self ):
        """
        Do invalidations of potential dependencies, tied either to system group,
        or to the main provider tenancy group tied to the system.
        """
        if self.is_system:
            invalidate_group_system( namespace='tg' )
        else:
            invalidate_group_provider( self.provider_optional_id )

    @property
    def is_system( self ):
        return self.provider_optional is None

    @property
    @stash_method_rv
    def public_storage_path( self ):
        """
        For provider instances place any public files in provider location,
        otherwise use the system location.
        """
        if self.provider_optional:
            return self.provider_optional.public_storage_path
        else:
            return '_system'

    def clone( self, **kwargs ):
        """
        Cloning a system object must include Provider such that the
        clone is a new custom object.
        """
        if not ( self.provider_optional or 'provider_optional' in kwargs ):
            kwargs['provider_optional'] = kwargs.pop('provider')
        return super().clone( **kwargs )
