#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Base class for Provider models
"""
from django.db import models

from mpframework.common.cache import cache_rv
from mpframework.common.model import BaseModel
from mpframework.common.cache.stash import stash_method_rv

from .. import provider
from .tenant_clone import TenantCloneMixin


class ProviderModel( TenantCloneMixin, BaseModel ):
    """
    Base class for models partitioned on providers
    """
    _provider = models.ForeignKey( provider.Provider, models.CASCADE,
                                   db_column='provider_id' )

    class Meta:
        abstract = True

    # Used to manage shared tenant functionality
    _tenancy_type = '_provider'

    def __init__( self, *args, **kwargs ):
        super().__init__( *args, **kwargs )

    def provider_keyfn( self ):
        """
        Cache key invalidation group for dependencies on the provider
        """
        return '', 'prov{}'.format( self._provider_id )

    @property
    @cache_rv( keyfn=provider_keyfn )
    def provider( self ):
        return self._provider

    @property
    @stash_method_rv
    def public_storage_path( self ):
        return self.provider.public_storage_path
