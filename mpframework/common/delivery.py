#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared support for protection/compatibility modes

    MPF provides secure delivery of online content. Due to
    different customer needs and many compatibility edge case
    issues with various browsers, firewalls, etc. different
    delivery modes are supported by the framework. These modes
    ultimately affect the URLs used by the system based on
    various levels of settings and per-request options.

    See content/delivery.py for a description of how protected
    files are managed for the different modes.
"""
from django.conf import settings

from .utils.paths import path_extension


"""-------------------------------------------------------------------
    Delivery constants

    BALANCE - Signed url, session checked
    PROT    - Adds IP to signed url, lowers timeout
    COMP    - Signed url, session NOT checked
    OPEN    - Public content through alternative CF distribution

    COOKIE  - Use cookie for signed URL
    QUERY   - Use query string for signed URL
    NGINX   - Serve direct from Nginx
    LMS     - Hybrid mode based on file types, Nginx for small (CORS iframe issues),
              CF query for video (biggest performance driver)

    DEFAULT - The current system default for delivery
    PARENT  - For group, user overrides, specifies upstream default is used
"""
DELIVERY_PARENT = ''

DELIVERY_PROT    = 'prot'
DELIVERY_BALANCE = 'balance'
DELIVERY_COMP    = 'comp'
DELIVERY_OPEN    = 'open'

DELIVERY_COOKIE  = 'cookie'
DELIVERY_QUERY   = 'query'
DELIVERY_NGINX   = 'nginx'
DELIVERY_LMS     = 'lms'

DELIVERY_PROT_COOKIE    = 'prot-cookie'
DELIVERY_PROT_QUERY     = 'prot-query'
DELIVERY_BALANCE_COOKIE = 'balance-cookie'
DELIVERY_BALANCE_QUERY  = 'balance-query'
DELIVERY_COMP_COOKIE    = 'comp-cookie'
DELIVERY_COMP_QUERY     = 'comp-query'
DELIVERY_COMP_LMS       = 'comp-lms'
DELIVERY_PROT_NGINX     = 'prot-nginx'
DELIVERY_COMP_NGINX     = 'comp-nginx'

DELIVERY_DEFAULT = DELIVERY_BALANCE_COOKIE

DELIVERY_MODES_MAIN = (
    ( DELIVERY_PROT_COOKIE,     u"More protection" ),
    ( DELIVERY_DEFAULT,         u"Balance protection and compatibility" ),
    ( DELIVERY_COMP_QUERY,      u"More compatibility" ),
    )
DELIVERY_MODES_EXTRA = (
    ( DELIVERY_BALANCE_QUERY,   u"Balanced - query" ),
    ( DELIVERY_COMP_LMS,        u"LMS compatibility" ),
    ( DELIVERY_COMP_COOKIE,     u"Compatibility - cookie" ),
    ( DELIVERY_PROT_QUERY,      u"Protection - query" ),
    ( DELIVERY_PROT_NGINX,      u"Protection - No CDN" ),
    ( DELIVERY_COMP_NGINX,      u"Compatibility - No CDN" ),
    ( DELIVERY_OPEN,            u"Only hide links (most compatibility)" ),
    )

# All choices related to delivery logic
DELIVERY_MODES = DELIVERY_MODES_MAIN + DELIVERY_MODES_EXTRA
DELIVERY_TYPES = tuple( key for key, value in DELIVERY_MODES )

# Choices for fields that can override, with blank for default / no override
DELIVERY_MODES_STAFF = (
    ( DELIVERY_PARENT, u"Use default" ),
    ) + DELIVERY_MODES_MAIN
DELIVERY_MODES_ALL = DELIVERY_MODES_STAFF + DELIVERY_MODES_EXTRA


"""-------------------------------------------------------------------
    Helper functions
"""

def use_compatibility( mode ):
    return any( mode.startswith( m ) for m in [
                    DELIVERY_OPEN, DELIVERY_COMP ])

def use_querystring_url( mode ):
    return mode in [
            DELIVERY_PROT_QUERY,
            DELIVERY_BALANCE_QUERY,
            DELIVERY_COMP_QUERY,
            DELIVERY_COMP_LMS,
            ]

def use_open( mode ):
    if mode:
        return mode.startswith( DELIVERY_OPEN )

def use_no_auth( mode ):
    """
    Compatibility setting to work around lost Django session cookie situations
    MAKES ACCESS URL PUBLIC WHILE access_session IS IN CACHE
    """
    return mode.startswith( DELIVERY_COMP ) or use_open( mode )

def use_signed( mode, path=None ):

    # The following delivery modes use CF for ALL content
    rv = mode in [
            DELIVERY_PROT_COOKIE,
            DELIVERY_PROT_QUERY,
            DELIVERY_BALANCE_COOKIE,
            DELIVERY_BALANCE_QUERY,
            DELIVERY_COMP_COOKIE,
            DELIVERY_COMP_QUERY,
            ]

    # If path is provided, use CF in these modes with certain files
    if not rv and path and mode in [
            DELIVERY_COMP_LMS,
            ]:
        ext = path_extension( path )
        rv = ext in settings.MP_FILE['VIDEO_TYPES']

    return rv
