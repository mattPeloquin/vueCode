#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    A "provider" represents a company providing content
"""
from django.db import models
from django.conf import settings

from mpframework.common import log
from mpframework.common import constants as mc
from mpframework.common.model import BaseModel
from mpframework.common.model import CachedModelMixin
from mpframework.common.model.contact_mixin import ContactMixin
from mpframework.common.model.fields import YamlField
from mpframework.common.cache.stash import stash_method_rv
from mpframework.common.cache.groups import cache_group_provider
from mpframework.common.cache.groups import invalidate_group_provider
from mpframework.common.utils import join_urls

from ..signals import provider_change
from .base import TenantManager


class ProviderManager( TenantManager ):
    """
    Root staff are the only ones that manipulate providers through the staff
    admin, and that is fairly basic.
    """

    def create_obj( self, **kwargs ):
        """
        Add a new provider to the system
        """
        kwargs['resource_path'] = kwargs.get( 'resource_path', kwargs['system_name'] )
        rv = super().create_obj( **kwargs )
        log.info("CREATED PROVIDER: %s", rv)
        return rv


class Provider( ContactMixin, CachedModelMixin, BaseModel ):
    """
    Represents the relationship with a provider that is providing/selling
    product on a given root instance
    """

    # System name
    # Used for internal references and some name stamping
    system_name = models.CharField( unique=True, max_length=mc.CHAR_LEN_UI_LONG )

    # Storage folder (no spaces, valid path)
    # Defines path for provider-specific resources
    # MUST KEEP SYNCED WITH S3 PROVIDER FOLDERS
    resource_path = models.CharField( max_length=mc.CHAR_LEN_UI_LONG )

    # Full name used to refer to provider in UI
    name = models.CharField( max_length=mc.CHAR_LEN_UI_DEFAULT )

    """
    Are sandboxes for this provider visible to each other?

    'True' provides reseller capability, where each sandbox is
    treated as a separate customer. This includes:
        - The MTM content-sandbox relationship is never exposed.
        - Provider cache invalidation occurs within sandboxes vs. provider.

    'False' allows sandboxes to share content and treats all sandboxes
    under the provider as belonging to the same account.
    """
    isolate_sandboxes = models.BooleanField( default=False )

    # Flexible schema for system, provider, and site options
    # Never seen by staff or users
    policy = YamlField( null=True, blank=True )

    # Is the provider account active
    is_active = models.BooleanField( default=True )

    # Internal information
    root_notes = models.CharField( max_length=mc.CHAR_LEN_DB_SEARCH, blank=True )

    objects = ProviderManager()

    def __str__(self):
        if settings.DEBUG:
            return "{}p{}({})".format( self.system_name, self.pk, id(self) )
        else:
            return self.system_name

    def _log_instance( self, message ):
        log.debug_on() and log.detail("%s Provider: %s", message, self)

    def save( self, *args, **kwargs ):
        super().save( *args, **kwargs )
        provider_change.send( sender=self.pk )

    @property
    @stash_method_rv
    def cache_group( self ):
        """
        Chain provider instances to system group, which separates invalidating a
        provider instance from invalidating items with provider scope.
        Stash the value so provider obj upstream chaining will not change
        its cache group during obj lifetime.
        """
        return cache_group_provider( self.pk, system=True )

    def invalidate_group( self ):
        invalidate_group_provider( self.pk )

    @property
    def public_storage_path( self ):
        # Unless overridden, provider public material under its own top-level folder
        return self.policy.get( 'storage.provider_public', self.resource_path )

    @property
    def protected_storage_path( self ):
        # Unless overridden, each provider has top-level protected folder
        return self.policy.get( 'storage.provider_protected', self.resource_path )

    @property
    def content_public_storage( self ):
        """
        Content public files go under one folder under provider
        """
        return self.policy.get( 'storage.content_public',
                        join_urls( self.public_storage_path, '_content' ) )
    @property
    def content_media_url( self ):
        return join_urls( settings.MEDIA_URL, self.content_public_storage )

    @property
    def is_root( self ):
        """
        HACK - Root provider is hard-coded as the first provider
        """
        return self.pk == settings.MP_ROOT['PROVIDER_ID']
