#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Logic for finding/loading custom templates,
    usually via the mp_include tag
"""
from django.db.models import Q

from mpframework.common import log
from mpframework.common.logging.timing import mpTiming
from mpframework.foundation.tenant.models.base import TenantManager


class TemplateCustomManager( TenantManager ):

    def get_custom( self, name, sandbox=None, template_type=None ):
        """
        Returns TemplateCustom object or None if template does not exist in DB.

        Implement overrides of templates by checking for sandbox, then provider,
        then system for custom template name.
        Most templates will only be checked by the name used in mp_include, but
        Override templates also look at orig_path.
        """

        # Blank or none values can be passed for templates that are not set
        if not name:
            return

        # Custom templates can be passed into mp_include when they are loaded
        # from context variables, in which case just return it
        if isinstance( name, self.model ):
            return name

        rv = None
        if log.debug_on():
            log.detail3("Trying to get template: %s -> %s", sandbox, name)
            t = mpTiming( db=False )

        # Look in both name and optional script name
        q_name = Q( name=name ) | Q( _script_name=name )

        # Add template type to some searches
        q_filt = {}
        if template_type:
            q_filt['template_type'] = template_type

        # There can only be one exact match per provider, but that match can
        # be applied to a subset of sandboxes
        if sandbox:
            rv = self.get_quiet( q_name, provider_optional=sandbox.provider, **q_filt )
            if rv and not rv.all_sandboxes:
                if not sandbox in rv.sandboxes:
                    rv = None

        # If no match for Provider and Sandbox, try system-wide match
        if not rv:
            rv = self.get_quiet( q_name, provider_optional=None, **q_filt )

        log.debug_on() and log.debug2("Template load(%s) %s -> %s",
                                         t.log_total, sandbox, name )
        return rv

    def template_list( self, sandbox, types, *args, **kwargs ):
        """
        Return list of all templates of the requested type that can
        be used with the sandbox.
        """
        rv = []
        qs = self.mpusing('read_replica').filter( *args,
                provider_optional_system=sandbox.provider,
                template_type__in=types, **kwargs )
        for template in qs.iterator():
            if template.all_sandboxes or sandbox in template.sandboxes:
                rv.append( template )
        return rv
