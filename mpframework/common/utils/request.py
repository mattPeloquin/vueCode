#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    HTTP and request utilities specific to Django apps
"""
from hashlib import sha1
from django.conf import settings

from .. import log
from .. import constants as mc
from ..compat import compat_public
from .http import IP_RE
from .http import join_urls
from .http import append_querystring
from . import memoize


QUERYSTRING_POPUP = '_popup'
QUERYSTRING_PREFIX = 'vu_'


def is_api_request( request ):
    """
    Extend Django's is_ajax to include all requests with ACCEPT set to
    application/json. This allows simple ajax requests that don't cause
    CORS OPTIONS request cross-domain.
    """
    return ( request.META.get('HTTP_ACCEPT') == 'application/json' or
             request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest' )

def lazyrequest( fn, request, *args, **kwargs ):
    """
    Lazy execution and memoization for functions used with requests
    (particularly context_processors).
    When used with template caching, an expensive operation for a value
    accessed in a cached template fragment is only hit once.
    NOTE - fn name must be unique in the request.mpstash namespace.
    """
    fn = memoize( fn, request.mpstash )
    def wrapper():
        return fn( request, *args, **kwargs )
    return wrapper

def get_full_redirect( request, url=None ):
    """
    Return a redirect path that includes querystrings sent across redirects.
    """
    pairs_to_keep = {}
    url = url or request.path
    for name, value in request.GET.items():
        if name.startswith( QUERYSTRING_PREFIX ):
            pairs_to_keep[ name ] = value
    return append_querystring( url, **pairs_to_keep )

def get_ip( request ):
    """
    Retrieve remote IP address from the request data,
    return blank if it cannot be resolved.
    If the user is behind a proxy, they may have a comma-separated list
    of IP addresses; only the first IP is used.
    AWS ELB puts the REMOTE_ADDR into X-FORWARDED-FOR
    """
    rv = None
    ip_address = request.META.get( 'HTTP_X_FORWARDED_FOR',
                                        request.META.get('REMOTE_ADDR') )
    if ip_address:
        try:
            address_match = IP_RE.match( ip_address )
            if address_match:
                rv = str( address_match.group(0) )
        except IndexError:
            pass
        if not rv:
            log.info("SUSPECT - IP address: %s -> %s", ip_address, request.META)
    return rv

def get_referrer( request, max_len=mc.CHAR_LEN_PATH ):
    rv = ''
    try:
        url = request.META.get( 'HTTP_REFERER', '' )
        rv = str( url[ :max_len ] )
    except Exception:
        log.info2("Referrer error: %s", request.mpipname)
        if settings.MP_TESTING:
            raise
    return rv

#--------------------------------------------------------------------
# Shared Edge server support

HOST_DIGEST_LENGTH = 16

def edge_version( request, version ):
    """
    Fixup version tags used to invalidate browser caching with edge server URLs:

        1) Multiple host names and CORS
        Add hash of origin to key version value used for edge AJAX URLs.
        This is necessary because if multiple host names are used and user
        switches between them their browser can cache origin header of original,
        which will cause CORS cross-origin errors with AJAX calls.
    """
    host_name = str( request.host ).encode( 'utf-8', 'replace' )
    # sha1 hexdigest is 40 chars long, just grab start
    host_name = sha1( host_name ).hexdigest()[ :HOST_DIGEST_LENGTH ]
    return '{}_{}'.format( version, host_name )

def edge_public_url( request, url ):
    """
    For cloud deployments adds edge public to the relative url,
    with compatibility processing.
    """
    edge = settings.MP_ROOT_URLS['URL_PUBLIC']
    rv = join_urls( edge, url, scheme=True )
    rv = compat_public( rv, request.user.use_compat_urls )
    return rv
