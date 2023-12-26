#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Base Content Item Manager adds support for managing the
    sandboxes MTM relationship.

    Content workflow is NOT managed here with user_filter or another
    default mechanism because multiple workflow__in filter args are ADDITIVE,
    so setting up automatic defaults is complicated. Instead, workflow is
    explicitly managed in fixed manager methods or workflow__in as needed.
    NOTE - by convention use workflow__in='' instead of workflow=''
    in all cases to support easy searching.
"""
from mpframework.common import log
from mpframework.foundation.tenant.query_filter import tenant_filter_parse
from mpframework.foundation.tenant.query_filter import tenant_filter_args
from mpframework.foundation.tenant.models.base import TenantManager
from mpframework.foundation.tenant.models.base import TenantQuerySet


class ContentQuerySet( TenantQuerySet ):

    def _filter_args( self, *args, **kwargs ):
        """
        Content-specific additions to tenant filter processing
        """
        kwargs = tenant_filter_parse( **kwargs )

        # Support staff with sandboxes privledge seeing content not tied
        # to their current sandbox in admin (so it could be assigned)
        admin = kwargs.get( 'admin_filter', None )
        if admin:
            user = kwargs.get( 'user_filter', None )
            if user and user.sees_sandboxes:
                # Popping any sandbox forces use of user provider
                kwargs.pop( 'sandbox', None )

        return tenant_filter_args( self.model, *args, **kwargs )

class _ContentManager( TenantManager ):

    def _get_queryset( self ):
        """
        Force use of item manager (vs. TenantManager) in downstream inheritance
        """
        return ContentQuerySet( model=self.model )

    def get_queryset( self ):
        return self._get_queryset()

    def active( self ):
        return self.mpusing('read_replica')\
                    .exclude( workflow__in='R' )

    def limits_ok( self, **kwargs ):
        """
        Validate any limits
        """
        provider = kwargs['_provider']
        content_limit = provider.policy.get('site_limits.max_content')

        if content_limit:
            items = self.filter( _provider=provider ).count()
            if items >= content_limit:
                log.info("SUSPECT LIMIT: Attempt to exceed content: %s -> %s",
                        provider, items)
                return False

        return True

    def create_obj( self, **kwargs ):
        """
        Create a new content object; can use minimal information
        as a placeholder or with as much information as provided.
        Sandbox is normally provided; it is translated into a provider
        and content-sandbox relationship.
        """
        kwargs['_name'] = kwargs.pop( 'name', kwargs.get('_name') )
        # Provider may be defined as sandbox or explicitly
        sandbox = kwargs.pop( 'sandbox', None )
        if sandbox:
            kwargs['_provider'] = sandbox.provider

        item = super().create_obj( **kwargs )

        if sandbox and item:
            item.sandboxes.add( sandbox )

        return item

    def clone_sandbox_objects( self, source, target ):
        """
        Add respecting content sandboxes setting to cloning
        """
        filters = {
            'sandboxes': source.pk,
            }
        return super().clone_sandbox_objects( source, target, **filters )

# Use from_queryset to include both custom manager and queryset methods
ContentManager = _ContentManager.from_queryset( ContentQuerySet )
