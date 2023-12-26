#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared content model code for visibility and workflow
"""
from django.db import models
from django.db.models.signals import m2m_changed

from mpframework.common import log
from mpframework.common.cache import stash_method_rv
from mpframework.foundation.tenant.models.sandbox import Sandbox

from ...cache import cache_group_content
from ...cache import invalidate_group_content
from ...cache import invalidate_group_content_timewin_sandbox


class BaseContentVisibility( models.Model ):
    """
    Metadata used with all content models related to:
      - Sandboxes content is attached to
      - Workflow
      - User visibility
    """

    # The Sandboxes this item is visible in
    sandboxes = models.ManyToManyField( Sandbox, blank=True )

    # Content workflow
    # The Retired workflow state is managed through ContentManager, while the
    # other states are managed more as UI visibility flags.
    WORKFLOW_STATE_ACTIVE = (
        ('P', u"Production"),       # All users can see
        ('B', u"Beta"),             # Users with beta access can see
        ('D', u"Development"),      # Only staff can see
        )
    WORKFLOW_STATE_RETIRED = (
        ('Q', u"Prod Retire"),      # Only users that had/bought this item can see
        ('R', u"Retired"),          # Can only be seen in certain admin views
        )
    WORKFLOW_STATES = WORKFLOW_STATE_ACTIVE + WORKFLOW_STATE_RETIRED
    workflow = models.CharField( max_length=1, choices=WORKFLOW_STATES, default='P' )

    class Meta:
        abstract = True

    # Specializations must set this to name of sandbox through-table field for own id
    sandbox_through_id = ''

    # Sandboxes are mostly referenced in admin, so only get extra there
    prefetch_related = ()
    prefetch_related_admin = ( 'sandboxes' ,)

    # Allow sees_sandboxes users to see all provider content in any sandbox
    provider_staff_sees_sandboxes = True

    @property
    @stash_method_rv
    def sandbox_ids( self ):
        """
        Optimized call to get set of sandbox ids for filtering
        """
        return set( self.sandboxes.all().values_list( 'id', flat=True ) )

    @property
    def provider_id( self ):
        """
        Support use and caching of content derived from ProviderOptional.
        Returns 0 as special case for system content.
        """
        return ( getattr( self, '_provider_id', None ) or
                self.provider_optional_id or 0 )

    @property
    @stash_method_rv
    def cache_group( self ):
        """
        Content cache group invalidation is based on any content changes
        within the scope the content can be seen, which is provider or 1 sandbox
        depending on the isolate sandbox settings.
        Content cache scope is separate from provider and sandbox cache groups
        so key provide/sandbox performance caching like template fragment caching
        is not invalidated with every content change.
        """
        return cache_group_content( self.provider_id,
                    getattr( self, 'isolate_sandbox', False ) )

    def invalidate_group( self ):
        invalidate_group_content( self.provider_id,
                    getattr( self, 'isolate_sandbox', False ) )


    def workflow_higher( self, workflow ):
        # Return true if THIS item is more permissive than the given workflow
        if self.workflow == workflow:
            return False
        if self.workflow in ['P','Q']:
            return True
        if self.workflow in ['B']:
            return workflow in ['D','R']
        if self.workflow in ['D']:
            return workflow in ['R']

    @property
    def is_retired( self ):
        return self.workflow in ['R','Q']

    @property
    def is_fully_retired( self ):
        return self.workflow in ['R']


def _sandboxes_change( sender, **kwargs ):
    """
    When items removed from a sandbox, timewin caching has no easy way to
    detect the removal. Instead of adding a deletion mechanism to the timewin
    caching, cause a sandbox-wide invalidation since this is infrequent.
    """
    if kwargs.get('reverse'):
        return
    if kwargs.get('action') == 'post_remove':
        item = kwargs.get('instance')
        log.debug("Removing item from sandbox: %s", item)
        for sandbox_id in kwargs.get('pk_set'):
            invalidate_group_content_timewin_sandbox( sandbox_id )

m2m_changed.connect( _sandboxes_change,
                     sender=BaseContentVisibility.sandboxes.through )
