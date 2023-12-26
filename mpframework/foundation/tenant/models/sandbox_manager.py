#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Sandbox Manager and related utilities
"""
from django.conf import settings

from mpframework.common import log
from mpframework.common.cache import cache_rv
from mpframework.common.cache.groups import cache_group_sandbox
from mpframework.common.utils.hosts import fixup_host_name

from .base import TenantManager


class SandboxManager( TenantManager ):
    """
    Sandboxes are owned by providers

    Some sandbox information is accessed frequently so should be
    cached, but have callers do that based on context vs. here
    """

    def get_sandbox_from_host( self, hostname ):
        """
        Return sandbox that matches the host url (of which a sandbox can have many)
        Throws exception if sandbox not found
        Usually this is only used to get a sandbox id mapping to a host,
        that is then cached and used to access a sandbox object that itself
        can be cached to share across hosts.
        """
        hostname = fixup_host_name( hostname )
        return self.get( hosts___host_name=hostname )

    def get_sandbox_from_id( self, id, provider_id=None ):
        """
        MAIN ACCESS POINT FOR LOADING SANDBOX OBJECTS FOR REQUESTS
        Get sandbox from id, adds additional info, and places into cache;
        provider_id ties cached sandbox to the provider cache group.
        """
        try:
            return self._get_sandbox_from_id( id, provider_id )
        except self.model.DoesNotExist:
            if settings.MP_DEV_EXCEPTION:
                raise
            log.warning("SUSPECT - Bad sandbox: %s, %s", id, provider_id)

    @cache_rv( keyfn=lambda _, id, provider_id:(
                cache_group_sandbox( id, provider_id ), '' ) )
    def _get_sandbox_from_id( self, id, _provider_id ):
        """
        Shared cache for the sandbox object, using the main tenancy cache group.
        The cached sandbox state is from DB values only.
        """
        rv = self.get( id=id )
        log.debug("Sandbox from id: %s", rv)
        return rv

    def subdomain_ok( self, subdomain ):
        """
        Check that requested subdomain is valid and not in use as sandbox subdomain or
        as an additional hostname as subdomain of the root site.
        Returns a valid subdomain if ok or None
        """
        rv = None
        try:
            # Check that subdomain is a reasonable string
            _subdomain = str( subdomain ).strip()
            if len( _subdomain ) >= settings.MP_INVALID_SUBDOMAIN['MIN_LEN']:
                try:
                    int( _subdomain )
                except Exception:
                    if( not any( _subdomain == w for w in settings.MP_INVALID_SUBDOMAIN['WORDS'] ) and
                        not _subdomain.startswith( tuple(settings.MP_INVALID_SUBDOMAIN['START']) ) and
                        not any( c in _subdomain for c in settings.MP_INVALID_SUBDOMAIN['CHARS'] )
                        ):
                        rv = _subdomain

            # Check it doesn't already exist
            if rv and self.filter( subdomain=rv ).exists():
                rv = None
            if rv:
                hostname = '{}.{}'.format( rv, settings.MP_ROOT['HOST'] )
                hostname = fixup_host_name( hostname )
                if self.filter( hosts___host_name=hostname ).exists():
                    rv = None

        except Exception:
            log.exception("Subdomain request: %s", subdomain)
        log.info3("SUBDOMAIN %s AVAILABLE: %s", 'IS' if rv else 'NOT', subdomain)
        return rv

    def clone_sandbox( self, source, provider, name, subdomain, **kwargs ):
        """
        Returns a new sandbox using the given source sandbox as a "template"
        to clone data into new sandbox attached to the given provider.
        Field values in the source can be overridden in sitebuilder data.
        """
        log.info("Cloning sandbox: %s -> %s", source, source.options['clone'])

        # Setup any fields from source, and then args
        extra_fields = {}
        for key, value in source.options['clone'].items():
            extra_fields[ key ] = value
        for key, value in kwargs.items():
            extra_fields[ key ] = value

        # Clone/save the new sandbox and then get it to verify creation
        # and force load/validate of fields from DB
        new_sand = source.clone( exclude_relationships=False, _provider=provider,
                    subdomain=subdomain, name=name, **extra_fields )
        rv = self.get( id=new_sand.pk )
        log.info("CLONED SANDBOX: %s -> %s", source, rv)
        return rv

    def clone_sandbox_objects( self, source, target, **filters ):
        """
        This should not be called for sandboxes
        """
        raise Exception("clone_sandbox_objects called on sandbox")

    def create_obj( self, **kwargs ):
        """
        Support test creation (sandboxes are usually cloned)
        """
        kwargs['name'] = kwargs.get( 'name', kwargs['subdomain'] )
        return super().create_obj( **kwargs )
