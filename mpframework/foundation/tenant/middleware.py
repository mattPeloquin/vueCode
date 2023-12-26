#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Mangage tenancy state for every request
"""
from django.conf import settings
from django.utils import timezone
from django.http import HttpResponseRedirect

from mpframework.common import log
from mpframework.common.middleware import mpMiddlewareBase
from mpframework.common.utils import SafeNestedDict
from mpframework.common.utils.hosts import fixup_host_name
from mpframework.common.delivery import DELIVERY_DEFAULT

from .cache import get_sandbox


_sts_header = settings.MP_HTTP_SECURITY.get('STS_HEADER')


class HealthCheckSandbox:
    """
    Dummy sandbox to use in health checks, which have no sandbox
    """
    pk = None
    id = None
    _provider_id = None
    provider = None
    is_root = None
    frame_site_id = None
    options = SafeNestedDict()
    delivery_mode = DELIVERY_DEFAULT
    def __str__( self ):
        return 'HealthCheckSandbox'


class SandboxMiddleware( mpMiddlewareBase ):
    """
    Sandbox middleware sets up the request sandbox information based on url, and
    is called before user session and all other processing except FirstLast

    "no-host" requests are URLs whose Sandbox is NOT part of their host name;
    instead sandbox id is included in the request path.
    They are used for cases such as Cloudfront origin requests where
    the sandbox cannot provided in the host name.
    """

    def process_request( self, request ):
        """
        Add sandbox to the request and set timezone
        """
        if request.is_bad:
            return
        if request.is_healthcheck:
            request.sandbox = HealthCheckSandbox()
            return

        # First try no-host lookup of sandbox by ID in no-host URL
        # from either the querystring or the first path position
        no_host_id = None
        if request.mppath.startswith( settings.MP_URL_NO_HOST ):
            log.debug("NO-HOST request: %s -> %s", request.ip, request.mppath)
            if request.mppath.startswith( settings.MP_URL_NO_HOST_FT ):
                # HACK - simulate request for root sandbox
                no_host_id = '1'
            else:
                no_host_id = request.GET.get( 'no_host_id', request.mppathsegs[1] )

        # If getting sandbox fails here, a 404 will be raised
        sandbox = get_sandbox( request, no_host_id )

        # If normal host request, redirect hosts if needed
        redirect = None
        status = None
        if not no_host_id:

            # Try to get the appropriate host
            host_filter = { '_host_name': fixup_host_name( request.host ) }
            if request.is_secure():
                host_filter['https'] = True
            host = sandbox.get_host( **host_filter )

            # Handle invalid or redirect hosts
            if not host or host.redirect_to_main:
                host = sandbox.main_host
                request.host = host.host_name
                redirect = 'https' if host.https else 'http'

            # Redirect when https/http typed wrong for a valid host without explicitly
            # alternate in Sandbox hosts
            if host.https and not request.is_secure():
                redirect = 'https'
                status = 301
            if not host.https and request.is_secure():
                redirect = 'http'

        if redirect:
            # Redirect now if the URL is anything but home
            if request.mppathsegs[0]:
                url = '{}://{}{}'.format( redirect, request.host,
                                            request.get_full_path() )
                log.info3("Host redirect, scheme: %s -> %s", sandbox, url )
                return HttpResponseRedirect( url, status=status )
            # For home (no path) note http/https and let home view redirect
            # to handle home page special cases
            else:
                request.mpscheme = redirect

        # Set the timezone for the request based on sandbox settings
        try:
            timezone.activate( sandbox.timezone )
        except Exception:
            log.exception("Setting timezone failed: %s", sandbox)

        # Set sandbox and log name for this request
        request.sandbox = sandbox
        request.mpname = "s{}".format( sandbox.pk )

        log.debug2("Set request sandbox: %s -> %s", sandbox, request.ip)


    def process_response( self, request, response ):

        # Add STS header if sandbox isn't a main non-https
        http_redirect = getattr( request, 'mpscheme', None ) == 'http'
        if not http_redirect or request.is_secure():
            response['strict-transport-security'] = _sts_header

        return response
