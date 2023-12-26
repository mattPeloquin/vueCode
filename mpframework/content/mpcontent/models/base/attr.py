#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Content model attributes
    Base class for ALL content models that have provider/sandbox
    and workflow relationships.
"""

from mpframework.common import log
from mpframework.common.model import CachedModelMixin
from mpframework.common.cache import cache_rv
from mpframework.common.cache import stash_method_rv
from mpframework.foundation.tenant.models.base.provider import ProviderModel

from .visibility import BaseContentVisibility
from .fields import BaseContentFields


class BaseAttr( BaseContentFields, BaseContentVisibility,
                CachedModelMixin, ProviderModel ):
    """
    Abstract model for behavior common to all content classes
    """
    class Meta:
        abstract = True

    @property
    @cache_rv( keyfn=ProviderModel.provider_keyfn, buffered='local_small' )
    def isolate_sandbox( self ):
        """
        Returns None if content is not assigned to any isolated sandbox, or
        the id of the sandbox if it is.
        Caching prevents need to join on Provider and sandboxes table.
        """
        if self._provider.isolate_sandboxes:
            # Get sandbox ids efficiently by using through table
            options = { self.sandbox_through_id: self.pk }
            sandboxes = list( self.sandboxes.through.objects.filter( **options ) )
            # Having 0 or >1 sandbox assigned to content in a single-sandbox scenario
            # is an error, but fail gracefully by going back to provider case
            if sandboxes:
                if len(sandboxes) > 1:
                    log.warning("Isolated sandbox content with >1 sandbox: %s", self)
                return sandboxes[0].pk
            else:
                log.warning("Isolated sandbox content without sandbox: %s", self)

    @property
    @stash_method_rv
    def public_storage_path( self ):
        # The provider defines the public storage page
        return self.provider.content_public_storage

    def health_check( self, save=True ):
        """
        Perform checks on content to ensure records are healthy, working
        out from the base classes as needed.
        """
        log.debug("Validating data health for content: %s", self)
        self._health_check()
        if save:
            self.save()

    def _health_check( self ):
        """
        This can be overridden in specializations to add functionality
        """
        pass
