#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    HTML template fragment caching

    MPF uses some dynamic HTML with deeply nested/chained Django template
    structures to keep code small and dry. Most dynamic HTML is based
    on a few key variables shared across sandbox users, so template fragment
    caching is used to avoid rendering HTML for every request.

    Values in cached template fragments:

        MUST BE SENT AND USED VIA JAVASCRIPT  (vs. template variables)

    Template fragment caching uses sandbox invalidation group, and can
    extend that with user values, and path.
    Invalidation is controlled by the sandbox cache group.

    ++++++   BE CAREFUL WITH THIS CACHING   +++++++
    Since it bypasses template logic, dev errors can lead to hard-to-diagnose
    bugs and possible disclosure of information between users
"""
from functools import wraps
from django.conf import settings

from .. import log
from ..utils import get_random_key
from .groups import cache_group_sandbox


# MONKEY PATCH
# Django make_template_fragment_key for better debugging
def _template_fragment_key( fragment_name, vary_on=() ):
    key = ''.join( var for var in vary_on )
    return '_'.join([ 'template', fragment_name, key ])
from django.core.cache import utils
utils.make_template_fragment_key = _template_fragment_key


# Prefix for query string keys that are included in template caching
QUERYSTRING_PREFIX_CACHE = 'mpc_'

# Is static compression turned on? If two servers are sharing
# a cache and using different compression settings, the sets of files
# they request will be quite different
_COMPRESSION = (
    str( settings.MP_COMPRESS['JS'] )[0] +
    str( settings.MP_COMPRESS['CSS'] )[0]
    )

# Header names added to request to control HTML fragment caching
_NO_CACHING = 'mp_template_no_cache'
_NO_PAGE_CACHING = 'mp_template_no_page_cache'
_FULL_PATH_CACHING = 'mp_template_full_path_cache'
_FULL_QUERY_CACHING = 'mp_template_full_query_cache'


def template_no_cache( view_fn ):
    """
    Decorator to ensure no template caching is used with view
    """
    @wraps( view_fn )
    def wrapper( request, *args, **kwargs ):
        setattr( request, _NO_CACHING, True )
        return view_fn( request, *args, **kwargs )
    return wrapper

def template_no_page_cache( view_fn ):
    """
    Disable page-based caching for the view
    """
    @wraps( view_fn )
    def wrapper( request, *args, **kwargs ):
        setattr( request, _NO_PAGE_CACHING, True )
        return view_fn( request, *args, **kwargs )
    return wrapper

def use_full_path_cache( request ):
    """
    Update a request to use full path caching in the template fragment caching
    """
    setattr( request, _FULL_PATH_CACHING, True )
    return request

def full_path_cache( view_fn ):
    """
    Decorator to force using full path in template caching
    """
    @wraps( view_fn )
    def wrapper( request, *args, **kwargs ):
        return view_fn( use_full_path_cache( request ), *args, **kwargs )
    return wrapper

def use_full_query_cache( request ):
    """
    Update a request to use all of the query string in fragment caching
    """
    setattr( request, _FULL_QUERY_CACHING, True )
    return request

#------------------------------------------------------------------
# These are used in lazy-calls defined in the tenant context processor

def template_cache_sandbox( request ):
    """
    Returns key for template caching based on sandbox options
    """
    key = '-'.join([
        _base_key( request ),
        _sandbox_key( request ),
        ])
    log.cache("CACHE TEMPLATE SANDBOX: %s", key)
    return key

def template_cache_page( request ):
    """
    Adds key page types to sandbox caching for portal, admin
    """
    key = '-'.join([
        _base_key( request ),
        _sandbox_key( request ),
        _page_key( request ),
        ])
    log.cache("CACHE TEMPLATE PAGE: %s", key)
    return key

def template_cache_auth( request ):
    """
    Adds user authentication to sandpage
    """
    key = '-'.join([
        _base_key( request ),
        _sandbox_key( request ),
        _page_key( request ),
        _auth_key( request ),
        ])
    log.cache("CACHE TEMPLATE AUTH: %s", key)
    return key

def template_cache_staff( request ):
    """
    Adds full set of privledges that can alter top menu, etc.
    """
    key = '-'.join([
        _base_key( request ),
        _sandbox_key( request ),
        _page_key( request ),
        _auth_key( request ),
        _staff_key( request ),
        ])
    log.cache("CACHE TEMPLATE USER: %s", key)
    return key

#------------------------------------------------------------------
# Components to build up templat cache keys

def _no_cache( request, cache_type ):
    # Bail out with unique key if this request shouldn't be cached
    rv = ''
    no_cache = ( settings.MP_COMPRESS.get('NO_TEMPLATE_CACHING') or
                    getattr( request, cache_type, False ) )
    if no_cache:
        log.cache2("NO CACHE TEMPLATE %s: %s -> %s", cache_type,
                    request.mpname, request.path)
        rv = '_NO_CACHE_{}'.format( get_random_key() )
    return rv

def _base_key( request ):
    # Baseline template caching depending on whether template compressing on
    return _no_cache( request, _NO_CACHING ) + _COMPRESSION

def _sandbox_key( request ):
    """
    Tie template caching to full invalidation chain of sandbox, provider,
    and system to pick up all potential template changes.
    """
    sandbox = request.sandbox
    if sandbox:
        return cache_group_sandbox( sandbox.pk, sandbox._provider_id, system=True )
    else:
        return 'NoSand'

def _page_key( request ):
    # Load optional items that may have been set in context
    page_attr = ''.join([
        str( request.is_page_staff )[0],
        str( request.is_popup )[0],
        str( getattr( request, 'is_no_page_top', False ) )[0],
        ])
    # Admin page templates are cached separate from all others
    if not request.is_page_admin:
        page_attr += ''.join([
            str( request.is_portal )[0],
            'c' if request.mpstash.get('portal_content') else '',
            # User settings like color2
            str( request.skin.cache_template_key( request.user ) ),
            # Templates can have dev versions
            str( request.user.workflow_dev )[0],
            ])
    # Should all or just select query strings be used in cache key
    # Be careful to avoid short circuiting caching
    include_query = getattr( request, _FULL_QUERY_CACHING, False )
    query_items = [ key + str(qs[:16]) for key, qs in request.GET.items() if
                include_query or key.startswith( QUERYSTRING_PREFIX_CACHE ) ]
    page_attr += ''.join( query_items )
    return _no_cache( request, _NO_PAGE_CACHING ) + page_attr

def _auth_key( request ):
    # Add key user rights to cache key
    user = request.user
    return ''.join([
        'Au' if user.is_authenticated else 'An',
        str( user.is_ready() )[0],
        str( user.access_staff_view )[0],
        str( user.use_compat_urls )[0],
        str( user.workflow_beta )[0],
        str( user.has_test_access )[0],
        ])

def _staff_key( request ):
    """
    Base caching on what is shown based on staff privileges.
    Note this can lead to a lot of cache fragmentation with staff settings,
    but accept that when moving UI logic from server to client JS not worth it.
    """
    user = request.user
    if user.staff_level:
        return ''.join([
            str( user.staff_level ),
            str( user.sandboxes_level ),
            str( user.staff_areas ),
            str( user.is_owner )[0],
            str( user.is_superuser )[0],
            ])
    return ''
